"""Strict experiment configuration loading and validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class ConfigError(ValueError):
    """Raised when an experiment configuration is invalid."""


@dataclass(frozen=True)
class DataConfig:
    symbols: tuple[str, ...]
    interval: str
    start: str
    end: str
    cache_dir: Path


@dataclass(frozen=True)
class PortfolioConfig:
    initial_capital: float
    gross_limit: float
    leverage_limit: float


@dataclass(frozen=True)
class MeanReversionConfig:
    window: int
    z_threshold: float


@dataclass(frozen=True)
class TrendFollowingConfig:
    fast_window: int
    slow_window: int


@dataclass(frozen=True)
class StrategyConfig:
    mean_reversion: MeanReversionConfig
    trend_following: TrendFollowingConfig


@dataclass(frozen=True)
class EvaluationPeriod:
    start: str
    end: str


@dataclass(frozen=True)
class ExperimentConfig:
    name: str
    data: DataConfig
    portfolio: PortfolioConfig
    strategies: StrategyConfig
    costs: dict[str, float]
    evaluation: dict[str, EvaluationPeriod]
    output_dir: Path
    source_path: Path


def _expect_keys(data: dict[str, Any], expected: set[str], context: str) -> None:
    unknown = set(data) - expected
    missing = expected - set(data)
    if unknown:
        raise ConfigError(f"Unknown {context} field(s): {', '.join(sorted(unknown))}")
    if missing:
        raise ConfigError(f"Missing {context} field(s): {', '.join(sorted(missing))}")


def _positive(value: Any, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"{name} must be numeric") from exc
    if number <= 0:
        raise ConfigError(f"{name} must be greater than zero")
    return number


def _positive_int(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ConfigError(f"{name} must be a positive integer")
    return value


def _resolve_path(raw: str, config_path: Path) -> Path:
    path = Path(raw)
    if path.is_absolute():
        return path
    project_root = config_path.parent.parent
    return (project_root / path).resolve()


def load_config(path: str | Path) -> ExperimentConfig:
    """Load a YAML configuration and reject missing, unknown, or unsafe values."""
    config_path = Path(path).resolve()
    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(f"Configuration not found: {config_path}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML in {config_path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise ConfigError("Configuration root must be a mapping")
    _expect_keys(
        raw,
        {"name", "data", "portfolio", "strategies", "costs", "evaluation", "output_dir"},
        "configuration",
    )

    data = raw["data"]
    _expect_keys(data, {"symbols", "interval", "start", "end", "cache_dir"}, "data")
    symbols = tuple(data["symbols"])
    if not symbols or any(not isinstance(symbol, str) or not symbol for symbol in symbols):
        raise ConfigError("data.symbols must contain at least one non-empty symbol")
    if data["interval"] != "6h":
        raise ConfigError("Only the validated 6h interval is currently supported")
    if data["start"] >= data["end"]:
        raise ConfigError("data.start must be earlier than data.end")

    portfolio = raw["portfolio"]
    _expect_keys(
        portfolio,
        {"initial_capital", "gross_limit", "leverage_limit"},
        "portfolio",
    )

    strategies = raw["strategies"]
    _expect_keys(strategies, {"mean_reversion", "trend_following"}, "strategies")
    mean_reversion = strategies["mean_reversion"]
    trend_following = strategies["trend_following"]
    _expect_keys(mean_reversion, {"window", "z_threshold"}, "mean_reversion")
    _expect_keys(trend_following, {"fast_window", "slow_window"}, "trend_following")
    fast_window = _positive_int(trend_following["fast_window"], "fast_window")
    slow_window = _positive_int(trend_following["slow_window"], "slow_window")
    if fast_window >= slow_window:
        raise ConfigError("trend_following.fast_window must be smaller than slow_window")

    costs = raw["costs"]
    if not isinstance(costs, dict) or set(costs) != {"low", "baseline", "high"}:
        raise ConfigError("costs must define exactly low, baseline, and high multipliers")
    cost_values = {name: _positive(value, f"costs.{name}") for name, value in costs.items()}
    if not cost_values["low"] < cost_values["baseline"] < cost_values["high"]:
        raise ConfigError("cost multipliers must satisfy low < baseline < high")

    evaluation = raw["evaluation"]
    if not isinstance(evaluation, dict) or not evaluation:
        raise ConfigError("evaluation must define at least one period")
    periods: dict[str, EvaluationPeriod] = {}
    for name, period in evaluation.items():
        _expect_keys(period, {"start", "end"}, f"evaluation.{name}")
        if period["start"] >= period["end"]:
            raise ConfigError(f"evaluation.{name}.start must be earlier than its end")
        if period["start"] < data["start"] or period["end"] > data["end"]:
            raise ConfigError(f"evaluation.{name} must fall inside the configured data range")
        periods[name] = EvaluationPeriod(start=period["start"], end=period["end"])

    return ExperimentConfig(
        name=str(raw["name"]),
        data=DataConfig(
            symbols=symbols,
            interval=data["interval"],
            start=data["start"],
            end=data["end"],
            cache_dir=_resolve_path(data["cache_dir"], config_path),
        ),
        portfolio=PortfolioConfig(
            initial_capital=_positive(portfolio["initial_capital"], "initial_capital"),
            gross_limit=_positive(portfolio["gross_limit"], "gross_limit"),
            leverage_limit=_positive(portfolio["leverage_limit"], "leverage_limit"),
        ),
        strategies=StrategyConfig(
            mean_reversion=MeanReversionConfig(
                window=_positive_int(mean_reversion["window"], "window"),
                z_threshold=_positive(mean_reversion["z_threshold"], "z_threshold"),
            ),
            trend_following=TrendFollowingConfig(
                fast_window=fast_window,
                slow_window=slow_window,
            ),
        ),
        costs=cost_values,
        evaluation=periods,
        output_dir=_resolve_path(raw["output_dir"], config_path),
        source_path=config_path,
    )
