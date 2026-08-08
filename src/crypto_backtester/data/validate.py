"""Schema and time-grid validation for research data."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

MARKET_COLUMNS = {
    "open_time",
    "close_time",
    "symbol",
    "open",
    "high",
    "low",
    "close",
    "volume",
}


class DataValidationError(ValueError):
    """Raised when data cannot be used safely by the pipeline."""


@dataclass(frozen=True)
class ValidationSummary:
    rows: int
    symbols: tuple[str, ...]
    duplicate_bars: int
    missing_grid_bars: int
    non_positive_prices: int
    non_finite_values: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _require_utc(series: pd.Series, name: str) -> None:
    if not isinstance(series.dtype, pd.DatetimeTZDtype) or str(series.dt.tz) != "UTC":
        raise DataValidationError(f"{name} must contain timezone-aware UTC timestamps")


def validate_market_data(
    frame: pd.DataFrame,
    *,
    symbols: tuple[str, ...],
    start: str,
    end: str,
    strict_grid: bool = False,
) -> ValidationSummary:
    """Validate market schema, values, symbol coverage, ordering, and 6h grid."""
    missing_columns = MARKET_COLUMNS - set(frame.columns)
    if missing_columns:
        raise DataValidationError(
            f"Market data is missing required columns: {', '.join(sorted(missing_columns))}"
        )
    if frame.empty:
        raise DataValidationError("Market data is empty")
    _require_utc(frame["open_time"], "open_time")
    _require_utc(frame["close_time"], "close_time")

    observed_symbols = tuple(sorted(frame["symbol"].dropna().unique()))
    expected_symbols = tuple(sorted(symbols))
    if observed_symbols != expected_symbols:
        raise DataValidationError(
            f"Symbol coverage mismatch: expected {expected_symbols}, observed {observed_symbols}"
        )

    numeric = frame[["open", "high", "low", "close", "volume"]]
    non_finite = int((~np.isfinite(numeric.to_numpy(dtype=float))).sum())
    non_positive = int((frame[["open", "high", "low", "close"]] <= 0).sum().sum())
    if non_finite:
        raise DataValidationError(f"Market data contains {non_finite} non-finite numeric values")
    if non_positive:
        raise DataValidationError(f"Market data contains {non_positive} non-positive prices")
    if (frame["volume"] < 0).any():
        raise DataValidationError("Market data contains negative volume")

    duplicates = int(frame.duplicated(["symbol", "open_time"]).sum())
    expected_index = pd.date_range(
        pd.Timestamp(start, tz="UTC"),
        pd.Timestamp(end, tz="UTC"),
        inclusive="left",
        freq="6h",
    )
    missing_grid = 0
    for symbol in symbols:
        symbol_times = frame.loc[frame["symbol"] == symbol, "open_time"]
        if not symbol_times.is_monotonic_increasing:
            raise DataValidationError(f"Bars for {symbol} must be monotonically increasing")
        observed = pd.DatetimeIndex(symbol_times.unique())
        missing_grid += len(expected_index.difference(observed))
    if strict_grid and (duplicates or missing_grid):
        raise DataValidationError(
            f"Invalid 6h grid: {duplicates} duplicate bars and {missing_grid} missing bars"
        )

    return ValidationSummary(
        rows=len(frame),
        symbols=observed_symbols,
        duplicate_bars=duplicates,
        missing_grid_bars=missing_grid,
        non_positive_prices=non_positive,
        non_finite_values=non_finite,
    )


def validate_risk_free_data(frame: pd.DataFrame) -> None:
    required = {"date", "dff_percent"}
    missing = required - set(frame.columns)
    if missing:
        raise DataValidationError(
            f"Risk-free data is missing required columns: {', '.join(sorted(missing))}"
        )
    if frame.empty:
        raise DataValidationError("Risk-free data is empty")
    _require_utc(frame["date"], "date")
    if frame["date"].duplicated().any():
        raise DataValidationError("Risk-free data contains duplicate dates")
    if not frame["date"].is_monotonic_increasing:
        raise DataValidationError("Risk-free dates must be monotonically increasing")
    if not np.isfinite(frame["dff_percent"].to_numpy(dtype=float)).all():
        raise DataValidationError("Risk-free data contains non-finite rates")
