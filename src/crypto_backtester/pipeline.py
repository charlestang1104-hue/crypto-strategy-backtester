"""End-to-end experiment orchestration and atomic artifact publication."""

from __future__ import annotations

import json
import platform
import shutil
import tempfile
from pathlib import Path

import pandas as pd

from crypto_backtester import __version__
from crypto_backtester.backtest import simulate_strategy
from crypto_backtester.config import ExperimentConfig, load_config
from crypto_backtester.costs import cost_scenarios, roll_slippage_estimates
from crypto_backtester.data.clean import align_risk_free, clean_market_data, prepare_market_returns
from crypto_backtester.data.download import ensure_cached_sources
from crypto_backtester.data.validate import validate_market_data, validate_risk_free_data
from crypto_backtester.metrics import calculate_metrics
from crypto_backtester.strategies import build_mean_reversion, build_trend_following


class PipelineError(RuntimeError):
    """Raised when an experiment stage fails."""


def _read_sources(market_path: Path, risk_free_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    try:
        market = pd.read_csv(market_path)
        risk_free = pd.read_csv(risk_free_path)
    except (OSError, pd.errors.ParserError) as exc:
        raise PipelineError(f"data loading failed: {exc}") from exc

    for column in ["open_time", "close_time"]:
        market[column] = pd.to_datetime(market[column], utc=True, errors="coerce")
    market["symbol"] = market["symbol"].astype(str)
    for column in ["open", "high", "low", "close", "volume"]:
        market[column] = pd.to_numeric(market[column], errors="coerce")
    risk_free["date"] = pd.to_datetime(risk_free["date"], utc=True, errors="coerce")
    risk_free["dff_percent"] = pd.to_numeric(risk_free["dff_percent"], errors="coerce")
    return market, risk_free[["date", "dff_percent"]].copy()


def validate_cached_data(config: ExperimentConfig) -> dict[str, object]:
    """Validate locally cached source files without using the network."""
    market_path, risk_free_path = ensure_cached_sources(config.data, allow_download=False)
    market, risk_free = _read_sources(market_path, risk_free_path)
    market_summary = validate_market_data(
        market,
        symbols=config.data.symbols,
        start=config.data.start,
        end=config.data.end,
        strict_grid=False,
    )
    validate_risk_free_data(risk_free)
    return {"market": market_summary.to_dict(), "risk_free_rows": len(risk_free)}


def _write_json(data: dict[str, object], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, allow_nan=False), encoding="utf-8")


def _publish_atomic(staging: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    backup = destination.with_name(destination.name + ".previous")
    if backup.exists():
        shutil.rmtree(backup)
    had_previous = destination.exists()
    try:
        if had_previous:
            destination.replace(backup)
        staging.replace(destination)
    except Exception:
        if destination.exists():
            shutil.rmtree(destination)
        if backup.exists():
            backup.replace(destination)
        raise
    else:
        if backup.exists():
            shutil.rmtree(backup)


def _prepare_research_data(
    config: ExperimentConfig,
    *,
    allow_download: bool,
) -> tuple[pd.DataFrame, dict[str, object]]:
    market_path, risk_free_path = ensure_cached_sources(config.data, allow_download=allow_download)
    market, risk_free = _read_sources(market_path, risk_free_path)
    raw_summary = validate_market_data(
        market,
        symbols=config.data.symbols,
        start=config.data.start,
        end=config.data.end,
        strict_grid=False,
    )
    validate_risk_free_data(risk_free)
    clean_market, cleaning_summary = clean_market_data(
        market,
        symbols=config.data.symbols,
        start=config.data.start,
        end=config.data.end,
    )
    aligned_risk_free = align_risk_free(
        risk_free,
        start=config.data.start,
        end=config.data.end,
    )
    market_returns = prepare_market_returns(clean_market, aligned_risk_free)
    summary = {
        "raw_validation": raw_summary.to_dict(),
        "cleaning": cleaning_summary.to_dict(),
        "analysis_rows": len(market_returns),
        "bars_per_symbol": int(len(market_returns) / len(config.data.symbols)),
    }
    return market_returns, summary


def _build_positions(
    config: ExperimentConfig,
    market_returns: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    prices = (
        market_returns.pivot(index="open_time", columns="symbol", values="close")
        .sort_index()
        .reindex(columns=config.data.symbols)
    )
    _, mean_reversion = build_mean_reversion(
        prices,
        window=config.strategies.mean_reversion.window,
        z_threshold=config.strategies.mean_reversion.z_threshold,
        gross_limit=config.portfolio.gross_limit,
    )
    _, trend_following = build_trend_following(
        prices,
        fast_window=config.strategies.trend_following.fast_window,
        slow_window=config.strategies.trend_following.slow_window,
        gross_limit=config.portfolio.gross_limit,
    )
    return {"mean_reversion": mean_reversion, "trend_following": trend_following}


def _run_and_write(
    config: ExperimentConfig,
    market_returns: pd.DataFrame,
    validation_summary: dict[str, object],
    staging: Path,
) -> None:
    from crypto_backtester.plotting import (
        plot_cost_sensitivity,
        plot_cumulative_pnl,
        plot_equity_curves,
        plot_prices_and_returns,
        plot_strategy_exposures,
    )

    metrics_dir = staging / "metrics"
    figures_dir = staging / "figures"
    metrics_dir.mkdir(parents=True)
    figures_dir.mkdir(parents=True)

    positions = _build_positions(config, market_returns)
    returns_wide = (
        market_returns.pivot(index="open_time", columns="symbol", values="simple_return")
        .sort_index()
        .reindex(columns=config.data.symbols)
        .fillna(0.0)
    )
    slippage = roll_slippage_estimates(market_returns)
    scenarios = cost_scenarios(slippage, config.costs)
    slippage.to_csv(metrics_dir / "slippage_estimates.csv", index=False)

    metric_rows: list[dict[str, object]] = []
    for period_name, period in config.evaluation.items():
        start = pd.Timestamp(period.start, tz="UTC")
        end = pd.Timestamp(period.end, tz="UTC")
        period_index = returns_wide.index[
            (returns_wide.index >= start) & (returns_wide.index < end)
        ]
        if period_index.empty:
            raise PipelineError(f"evaluation period {period_name} contains no bars")
        baseline_pnl: list[pd.DataFrame] = []

        for strategy_name, full_positions in positions.items():
            target = full_positions.reindex(period_index).fillna(0.0)
            period_returns = returns_wide.reindex(period_index).fillna(0.0)
            for scenario_name, cost_rate in scenarios.items():
                pnl, executed = simulate_strategy(
                    target,
                    period_returns,
                    initial_capital=config.portfolio.initial_capital,
                    gross_limit=config.portfolio.gross_limit,
                    leverage_limit=config.portfolio.leverage_limit,
                    proportional_cost=cost_rate,
                )
                row: dict[str, object] = {
                    "period": period_name,
                    "strategy": strategy_name,
                    "cost_scenario": scenario_name,
                    "proportional_cost": cost_rate,
                }
                row.update(
                    calculate_metrics(
                        pnl,
                        executed,
                        initial_capital=config.portfolio.initial_capital,
                    )
                )
                metric_rows.append(row)
                if scenario_name == "baseline":
                    baseline = pnl.copy()
                    baseline["strategy"] = strategy_name
                    baseline_pnl.append(baseline)

        period_metrics = pd.DataFrame([row for row in metric_rows if row["period"] == period_name])
        combined_pnl = pd.concat(baseline_pnl, ignore_index=True)
        plot_equity_curves(combined_pnl, figures_dir / f"{period_name}_equity_curves.png")
        plot_cumulative_pnl(
            combined_pnl,
            figures_dir / f"{period_name}_cumulative_net_pnl.png",
            config.portfolio.initial_capital,
        )
        plot_cost_sensitivity(
            period_metrics,
            figures_dir / f"{period_name}_cost_sensitivity.png",
        )

    metrics = pd.DataFrame(metric_rows)
    numeric_columns = metrics.select_dtypes(include="number").columns
    metrics[numeric_columns] = metrics[numeric_columns].round(8)
    metrics.to_csv(metrics_dir / "performance_summary.csv", index=False)
    _write_json(validation_summary, metrics_dir / "validation_summary.json")

    plot_prices_and_returns(market_returns, figures_dir / "market_overview.png")
    plot_strategy_exposures(positions, figures_dir / "strategy_exposures.png")

    shutil.copy2(config.source_path, staging / "config.yaml")
    metadata = {
        "experiment": config.name,
        "package_version": __version__,
        "python": platform.python_version(),
        "assets": list(config.data.symbols),
        "interval": config.data.interval,
        "sample_start": config.data.start,
        "sample_end": config.data.end,
        "anti_lookahead": "All executable positions use a one-bar signal lag.",
        "data_sources": [
            "https://data.binance.vision/",
            "https://fred.stlouisfed.org/series/DFF",
        ],
    }
    _write_json(metadata, metrics_dir / "run_metadata.json")


def run_experiment(
    config_or_path: ExperimentConfig | str | Path,
    *,
    allow_download: bool = True,
) -> Path:
    """Run a configured experiment and publish artifacts only after full success."""
    config = (
        config_or_path
        if isinstance(config_or_path, ExperimentConfig)
        else load_config(config_or_path)
    )
    market_returns, validation_summary = _prepare_research_data(
        config,
        allow_download=allow_download,
    )
    config.output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{config.name}-", dir=config.output_dir.parent))
    try:
        _run_and_write(config, market_returns, validation_summary, staging)
        _publish_atomic(staging, config.output_dir)
    except Exception as exc:
        if staging.exists():
            shutil.rmtree(staging)
        if isinstance(exc, (PipelineError, ValueError)):
            raise
        raise PipelineError(f"experiment {config.name} failed: {exc}") from exc
    return config.output_dir
