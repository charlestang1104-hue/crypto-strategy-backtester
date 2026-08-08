"""Rolling z-score mean-reversion strategy."""

from __future__ import annotations

import pandas as pd

from crypto_backtester.features import rolling_zscore, target_positions


def build_mean_reversion(
    prices: pd.DataFrame,
    *,
    window: int,
    z_threshold: float,
    gross_limit: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build raw signals and one-bar-lagged target positions."""
    zscore = rolling_zscore(prices, window)
    signal = pd.DataFrame(0.0, index=prices.index, columns=prices.columns)
    signal[zscore > z_threshold] = -1.0
    signal[zscore < -z_threshold] = 1.0
    positions = target_positions(signal, gross_limit=gross_limit, lag_bars=1)
    return signal, positions
