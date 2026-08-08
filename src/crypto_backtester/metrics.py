"""Performance and risk metrics with explicit 6h annualization."""

from __future__ import annotations

import numpy as np
import pandas as pd


def average_holding_days(position_wide: pd.DataFrame, *, hours_per_bar: int = 6) -> float:
    """Average consecutive non-zero same-sign run length across assets."""
    runs: list[int] = []
    for symbol in position_wide.columns:
        signs = np.sign(position_wide[symbol].fillna(0.0))
        current_run = 0
        previous = 0.0
        for value in signs:
            if value != 0 and value == previous:
                current_run += 1
            elif value != 0:
                if current_run:
                    runs.append(current_run)
                current_run = 1
            else:
                if current_run:
                    runs.append(current_run)
                current_run = 0
            previous = value
        if current_run:
            runs.append(current_run)
    return float(np.mean(runs) * hours_per_bar / 24.0) if runs else 0.0


def max_drawdown(values: pd.Series) -> float:
    """Return the worst peak-to-trough portfolio decline."""
    running_peak = values.cummax()
    drawdown = values.div(running_peak).sub(1.0)
    return float(drawdown.min())


def calculate_metrics(
    pnl: pd.DataFrame,
    executed_positions: pd.DataFrame,
    *,
    initial_capital: float,
    bars_per_year: int = 4 * 365,
) -> dict[str, float]:
    """Calculate performance, trading-activity, and downside-risk metrics."""
    if pnl.empty:
        raise ValueError("pnl cannot be empty")
    period_return = pnl["net_pnl"] / initial_capital
    mean_return = float(period_return.mean())
    volatility = float(period_return.std())
    downside = period_return[period_return < 0]
    downside_std = float(downside.std()) if len(downside) > 1 else float("nan")
    sharpe = np.sqrt(bars_per_year) * mean_return / volatility if volatility > 0 else np.nan
    sortino = (
        np.sqrt(bars_per_year) * mean_return / downside_std
        if np.isfinite(downside_std) and downside_std > 0
        else np.nan
    )

    final_net_value = float(pnl["net_value"].iloc[-1])
    years = len(period_return) / bars_per_year
    drawdown = max_drawdown(pnl["net_value"])
    annual_return = (
        (final_net_value / initial_capital) ** (1.0 / years) - 1.0
        if years > 0 and final_net_value > 0
        else np.nan
    )
    calmar = (
        annual_return / abs(drawdown) if np.isfinite(annual_return) and drawdown < 0 else np.nan
    )

    return {
        "gross_pnl_usdt": float(pnl["gross_pnl"].sum()),
        "net_pnl_usdt": final_net_value - initial_capital,
        "final_gross_value": float(pnl["gross_value"].iloc[-1]),
        "final_net_value": final_net_value,
        "gross_return": float(pnl["gross_value"].iloc[-1] / initial_capital - 1.0),
        "net_return": float(final_net_value / initial_capital - 1.0),
        "total_turnover_usdt": float(pnl["turnover"].sum()),
        "total_cost_usdt": float(pnl["cost"].sum()),
        "average_holding_days": average_holding_days(executed_positions),
        "sharpe_net": float(sharpe),
        "sortino_net": float(sortino),
        "calmar_net": float(calmar),
        "max_drawdown_net": drawdown,
    }
