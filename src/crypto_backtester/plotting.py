"""Deterministic, publication-quality research figures."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

COLORS = {
    "mean_reversion": "#2563eb",
    "trend_following": "#ea580c",
    "low": "#16a34a",
    "baseline": "#2563eb",
    "high": "#dc2626",
}


def _style() -> None:
    plt.style.use("seaborn-v0_8-whitegrid")
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.titleweight": "bold",
            "axes.titlesize": 12,
            "axes.labelsize": 10,
            "font.size": 9,
            "legend.frameon": False,
            "grid.alpha": 0.25,
        }
    )


def _save(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def plot_prices_and_returns(market_returns: pd.DataFrame, path: Path) -> None:
    _style()
    symbols = list(market_returns["symbol"].drop_duplicates())
    fig, axes = plt.subplots(len(symbols), 2, figsize=(13, 3.1 * len(symbols)), sharex="col")
    axes = np.atleast_2d(axes)
    for row, symbol in enumerate(symbols):
        subset = market_returns.loc[market_returns["symbol"] == symbol].copy()
        normalized = 100.0 * subset["close"] / subset["close"].iloc[0]
        axes[row, 0].plot(subset["open_time"], normalized, color="#0f172a", linewidth=1.0)
        axes[row, 0].set_title(f"{symbol} normalized close")
        axes[row, 0].set_ylabel("Index (100 = start)")
        axes[row, 1].plot(
            subset["open_time"], subset["simple_return"], color="#b91c1c", linewidth=0.55
        )
        axes[row, 1].axhline(0, color="#334155", linestyle="--", linewidth=0.7)
        axes[row, 1].set_title(f"{symbol} 6h simple return")
        axes[row, 1].set_ylabel("Return")
    fig.suptitle("Market sample: prices and returns", fontsize=15, fontweight="bold", y=1.01)
    fig.tight_layout()
    _save(fig, path)


def plot_strategy_exposures(positions: dict[str, pd.DataFrame], path: Path) -> None:
    _style()
    fig, axes = plt.subplots(len(positions), 2, figsize=(13, 4.2 * len(positions)))
    axes = np.atleast_2d(axes)
    for row, (name, frame) in enumerate(positions.items()):
        gross = frame.abs().sum(axis=1)
        axes[row, 0].plot(gross.index, gross, color=COLORS[name], linewidth=0.9)
        axes[row, 0].set_title(f"{name.replace('_', ' ').title()} gross target exposure")
        axes[row, 0].set_ylabel("USDT")
        for symbol in frame.columns:
            axes[row, 1].plot(frame.index, frame[symbol], linewidth=0.65, label=symbol)
        axes[row, 1].set_title(f"{name.replace('_', ' ').title()} target positions")
        axes[row, 1].set_ylabel("USDT")
        axes[row, 1].legend(ncol=len(frame.columns), loc="upper right")
    fig.tight_layout()
    _save(fig, path)


def plot_equity_curves(pnl: pd.DataFrame, path: Path) -> None:
    _style()
    fig, ax = plt.subplots(figsize=(12, 5.8))
    for strategy, subset in pnl.groupby("strategy", sort=False):
        ax.plot(
            subset["open_time"],
            subset["net_value"],
            color=COLORS[strategy],
            linewidth=1.6,
            label=strategy.replace("_", " ").title(),
        )
    ax.axhline(10_000, color="#475569", linestyle="--", linewidth=0.8, label="Initial capital")
    ax.set_title("Net portfolio value after estimated trading costs")
    ax.set_ylabel("Portfolio value (USDT)")
    ax.set_xlabel("UTC")
    ax.legend(ncol=3)
    fig.tight_layout()
    _save(fig, path)


def plot_cumulative_pnl(pnl: pd.DataFrame, path: Path, initial_capital: float) -> None:
    _style()
    fig, ax = plt.subplots(figsize=(12, 5.4))
    for strategy, subset in pnl.groupby("strategy", sort=False):
        subset = subset.sort_values("open_time").copy()
        subset["date"] = subset["open_time"].dt.floor("D")
        daily = subset.groupby("date", as_index=False)["net_value"].last()
        ax.plot(
            daily["date"],
            daily["net_value"] - initial_capital,
            color=COLORS[strategy],
            linewidth=1.6,
            label=strategy.replace("_", " ").title(),
        )
    ax.axhline(0, color="#475569", linestyle="--", linewidth=0.8)
    ax.set_title("Cumulative net PnL (daily sampled)")
    ax.set_ylabel("Net PnL (USDT)")
    ax.set_xlabel("UTC")
    ax.legend()
    fig.tight_layout()
    _save(fig, path)


def plot_cost_sensitivity(metrics: pd.DataFrame, path: Path) -> None:
    _style()
    strategies = list(metrics["strategy"].drop_duplicates())
    scenarios = [
        name for name in ["low", "baseline", "high"] if name in set(metrics["cost_scenario"])
    ]
    x = np.arange(len(strategies))
    width = 0.24
    fig, ax = plt.subplots(figsize=(10, 5.4))
    for index, scenario in enumerate(scenarios):
        subset = metrics.loc[metrics["cost_scenario"] == scenario].set_index("strategy")
        values = [subset.loc[strategy, "net_return"] for strategy in strategies]
        ax.bar(
            x + (index - 1) * width,
            values,
            width,
            label=scenario.title(),
            color=COLORS[scenario],
        )
    ax.axhline(0, color="#475569", linewidth=0.8)
    ax.set_xticks(x, [strategy.replace("_", " ").title() for strategy in strategies])
    ax.set_ylabel("Net return on initial capital")
    ax.set_title("Transaction-cost sensitivity")
    ax.legend()
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda value, _: f"{value:.0%}"))
    fig.tight_layout()
    _save(fig, path)
