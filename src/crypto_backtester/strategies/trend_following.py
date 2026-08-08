"""Fast/slow moving-average trend-following strategy."""

from __future__ import annotations

import pandas as pd

from crypto_backtester.features import moving_average_direction, target_positions


def build_trend_following(
    prices: pd.DataFrame,
    *,
    fast_window: int,
    slow_window: int,
    gross_limit: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build raw signals and one-bar-lagged target positions."""
    signal = moving_average_direction(
        prices,
        fast_window=fast_window,
        slow_window=slow_window,
    )
    positions = target_positions(signal, gross_limit=gross_limit, lag_bars=1)
    return signal, positions
