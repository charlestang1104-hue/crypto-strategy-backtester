import numpy as np
import pandas as pd

from crypto_backtester.strategies import build_mean_reversion, build_trend_following


def test_both_strategies_return_lagged_bounded_positions() -> None:
    index = pd.date_range("2024-01-01", periods=50, freq="6h", tz="UTC")
    prices = pd.DataFrame(
        {
            "a": [100 + index * 0.2 for index in range(50)],
            "b": [100 + (-1) ** index * 2 for index in range(50)],
        },
        index=index,
    )
    for signal, positions in [
        build_mean_reversion(prices, window=8, z_threshold=1.0, gross_limit=1_000),
        build_trend_following(prices, fast_window=3, slow_window=8, gross_limit=1_000),
    ]:
        assert positions.iloc[0].eq(0).all()
        assert (positions.abs().sum(axis=1) <= 1_000 + 1e-8).all()
        expected_direction = np.sign(signal.shift(1).fillna(0))
        actual_direction = np.sign(positions)
        assert actual_direction.equals(expected_direction)
