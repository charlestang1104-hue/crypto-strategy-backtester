import pandas as pd

from crypto_backtester.features import target_positions


def test_signal_at_t_cannot_change_position_at_t() -> None:
    index = pd.date_range("2024-01-01", periods=4, freq="6h", tz="UTC")
    signal = pd.DataFrame({"asset": [0.0, 1.0, -1.0, 0.0]}, index=index)
    positions = target_positions(signal, gross_limit=100.0)
    assert positions.loc[index[1], "asset"] == 0.0
    assert positions.loc[index[2], "asset"] == 100.0
    assert positions.loc[index[3], "asset"] == -100.0


def test_gross_exposure_never_exceeds_limit() -> None:
    index = pd.date_range("2024-01-01", periods=3, freq="6h", tz="UTC")
    signal = pd.DataFrame({"a": [1, 1, -1], "b": [1, 0, 1]}, index=index)
    positions = target_positions(signal, gross_limit=90.0)
    assert (positions.abs().sum(axis=1) <= 90.0 + 1e-8).all()
