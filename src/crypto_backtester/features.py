"""Reusable rolling features and exposure normalization."""

from __future__ import annotations

import numpy as np
import pandas as pd


def rolling_zscore(prices: pd.DataFrame, window: int) -> pd.DataFrame:
    """Return the rolling price z-score using only observations up to each bar."""
    rolling_mean = prices.rolling(window).mean()
    rolling_std = prices.rolling(window).std()
    return (prices - rolling_mean) / rolling_std


def moving_average_direction(
    prices: pd.DataFrame,
    *,
    fast_window: int,
    slow_window: int,
) -> pd.DataFrame:
    """Return {-1, 0, 1} based on fast/slow moving-average ordering."""
    if fast_window >= slow_window:
        raise ValueError("fast_window must be smaller than slow_window")
    fast = prices.rolling(fast_window).mean()
    slow = prices.rolling(slow_window).mean()
    direction = pd.DataFrame(0.0, index=prices.index, columns=prices.columns)
    direction[fast > slow] = 1.0
    direction[fast < slow] = -1.0
    return direction


def target_positions(
    signal: pd.DataFrame,
    *,
    gross_limit: float,
    lag_bars: int = 1,
) -> pd.DataFrame:
    """Lag signals and normalize each bar to the configured gross exposure cap."""
    if gross_limit <= 0:
        raise ValueError("gross_limit must be greater than zero")
    if lag_bars < 1:
        raise ValueError("lag_bars must be at least one to prevent lookahead")
    executable = signal.shift(lag_bars).fillna(0.0)
    gross_signal = executable.abs().sum(axis=1).replace(0.0, np.nan)
    weights = executable.div(gross_signal, axis=0).fillna(0.0)
    positions = weights * gross_limit
    if (positions.abs().sum(axis=1) > gross_limit + 1e-8).any():
        raise RuntimeError("Position normalization exceeded the gross exposure limit")
    return positions
