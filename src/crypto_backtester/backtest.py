"""Capital-aware, cost-aware portfolio simulation."""

from __future__ import annotations

import pandas as pd


def simulate_strategy(
    target_positions: pd.DataFrame,
    asset_returns: pd.DataFrame,
    *,
    initial_capital: float,
    gross_limit: float,
    leverage_limit: float,
    proportional_cost: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Simulate executed positions, drift, turnover, PnL, and non-negative equity."""
    if initial_capital <= 0 or gross_limit <= 0 or leverage_limit <= 0:
        raise ValueError("capital and exposure limits must be greater than zero")
    if proportional_cost < 0:
        raise ValueError("proportional_cost cannot be negative")
    if not target_positions.index.equals(asset_returns.index):
        raise ValueError("target position and return indices must match")
    if list(target_positions.columns) != list(asset_returns.columns):
        raise ValueError("target position and return columns must match")

    weights = target_positions.astype(float) / gross_limit
    net_value = float(initial_capital)
    previous_position = pd.Series(0.0, index=weights.columns)
    previous_return = pd.Series(0.0, index=weights.columns)
    rows: list[dict[str, float | pd.Timestamp]] = []
    executed_rows: list[pd.Series] = []

    for timestamp in asset_returns.index:
        returns_now = asset_returns.loc[timestamp].fillna(0.0).astype(float)
        drifted_previous = previous_position * (1.0 + previous_return)
        executable_limit = min(gross_limit, leverage_limit * max(net_value, 0.0))
        executed = weights.loc[timestamp].fillna(0.0) * executable_limit

        turnover = float((executed - drifted_previous).abs().sum())
        cost = float(proportional_cost * turnover)
        gross_pnl = float((executed * returns_now).sum())
        raw_net_pnl = gross_pnl - cost
        realized_net_pnl = max(raw_net_pnl, -net_value)
        net_value = max(net_value + realized_net_pnl, 0.0)

        rows.append(
            {
                "open_time": timestamp,
                "gross_pnl": gross_pnl,
                "raw_net_pnl": raw_net_pnl,
                "net_pnl": realized_net_pnl,
                "turnover": turnover,
                "cost": cost,
                "net_value": net_value,
            }
        )
        executed_rows.append(executed)

        if net_value <= 0:
            previous_position = pd.Series(0.0, index=weights.columns)
            previous_return = pd.Series(0.0, index=weights.columns)
        else:
            previous_position = executed
            previous_return = returns_now

    pnl = pd.DataFrame(rows)
    pnl["gross_value"] = initial_capital + pnl["gross_pnl"].cumsum()
    executed_positions = pd.DataFrame(executed_rows, index=asset_returns.index)
    executed_positions.index.name = asset_returns.index.name
    return pnl, executed_positions
