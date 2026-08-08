from __future__ import annotations

import pandas as pd
import pytest

from crypto_backtester.data.clean import align_risk_free, clean_market_data
from crypto_backtester.data.validate import DataValidationError, validate_market_data


def _raw_frame() -> pd.DataFrame:
    times = pd.to_datetime(
        [
            "2024-01-01 00:00Z",
            "2024-01-01 06:00Z",
            "2024-01-01 06:00Z",
            "2024-01-01 18:00Z",
            "2024-01-02 00:00Z",
            "2024-01-02 06:00Z",
        ],
        utc=True,
    )
    prices = [100.0, 101.0, 101.0, 200.0, 102.0, 103.0]
    return pd.DataFrame(
        {
            "open_time": times,
            "close_time": times + pd.to_timedelta(21_599, unit="s"),
            "symbol": "AAAUSDT",
            "open": prices,
            "high": [price * 1.01 for price in prices],
            "low": [price * 0.99 for price in prices],
            "close": prices,
            "volume": 10.0,
        }
    )


def test_cleaning_repairs_duplicates_gaps_and_jumps() -> None:
    cleaned, summary = clean_market_data(
        _raw_frame(),
        symbols=("AAAUSDT",),
        start="2024-01-01",
        end="2024-01-02 12:00",
    )
    assert summary.duplicate_bars_removed == 1
    assert summary.missing_bars_repaired == 1
    assert summary.jump_bars_repaired == 1
    assert len(cleaned) == 6
    repaired_close = cleaned.loc[
        cleaned["open_time"] == pd.Timestamp("2024-01-01 18:00Z"), "close"
    ].item()
    assert repaired_close == 101.0


def test_validation_rejects_non_positive_prices() -> None:
    frame = _raw_frame()
    frame.loc[0, "close"] = 0.0
    with pytest.raises(DataValidationError, match="non-positive"):
        validate_market_data(
            frame,
            symbols=("AAAUSDT",),
            start="2024-01-01",
            end="2024-01-02 12:00",
        )


def test_risk_free_alignment_never_uses_future_observation() -> None:
    source = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01", "2024-01-03"], utc=True),
            "dff_percent": [4.0, 6.0],
        }
    )
    aligned = align_risk_free(source, start="2024-01-01", end="2024-01-04")
    day_two = aligned.loc[aligned["open_time"] == pd.Timestamp("2024-01-02 12:00Z")]
    assert day_two["dff_percent"].item() == 4.0
    assert day_two["source_date"].item() == pd.Timestamp("2024-01-01", tz="UTC")
