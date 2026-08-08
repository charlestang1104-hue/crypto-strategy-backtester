"""Transparent transaction-cost estimators and scenarios."""

from __future__ import annotations

import numpy as np
import pandas as pd


def roll_slippage_estimates(market_returns: pd.DataFrame) -> pd.DataFrame:
    """Estimate one Roll-style proportional slippage value per asset."""
    required = {"symbol", "simple_return"}
    missing = required - set(market_returns.columns)
    if missing:
        raise ValueError(f"Missing return columns: {', '.join(sorted(missing))}")
    rows: list[dict[str, float | str]] = []
    for symbol, subset in market_returns.groupby("symbol", sort=True):
        returns = subset["simple_return"].dropna()
        paired = pd.concat([returns, returns.shift(1)], axis=1).dropna()
        covariance = float(paired.cov().iloc[0, 1]) if len(paired) >= 2 else 0.0
        rows.append(
            {
                "symbol": symbol,
                "lag1_covariance": covariance,
                "roll_slippage": float(np.sqrt(max(-covariance, 0.0))),
            }
        )
    return pd.DataFrame(rows)


def cost_scenarios(
    estimates: pd.DataFrame,
    multipliers: dict[str, float],
) -> dict[str, float]:
    """Scale the equal-weighted per-asset Roll estimate into named scenarios."""
    if "roll_slippage" not in estimates:
        raise ValueError("estimates must contain roll_slippage")
    base = float(estimates["roll_slippage"].mean())
    return {name: base * float(multiplier) for name, multiplier in multipliers.items()}
