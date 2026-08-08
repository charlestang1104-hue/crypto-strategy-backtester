"""Deterministic cleaning and risk-free alignment."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd

from crypto_backtester.data.validate import validate_market_data, validate_risk_free_data


@dataclass(frozen=True)
class CleaningSummary:
    duplicate_bars_removed: int
    missing_bars_repaired: int
    jump_bars_repaired: int

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


def clean_market_data(
    market: pd.DataFrame,
    *,
    symbols: tuple[str, ...],
    start: str,
    end: str,
    jump_threshold: float = 0.20,
) -> tuple[pd.DataFrame, CleaningSummary]:
    """Restore a complete grid and apply the documented close-price repair rule."""
    validate_market_data(market, symbols=symbols, start=start, end=end, strict_grid=False)
    full_index = pd.date_range(
        pd.Timestamp(start, tz="UTC"),
        pd.Timestamp(end, tz="UTC"),
        inclusive="left",
        freq="6h",
    )
    cleaned_frames: list[pd.DataFrame] = []
    duplicates = 0
    missing = 0
    jumps = 0
    for symbol in symbols:
        subset = market.loc[market["symbol"] == symbol].sort_values("open_time").copy()
        duplicates += int(subset.duplicated("open_time").sum())
        subset = subset.drop_duplicates("open_time", keep="last").set_index("open_time")
        subset = subset.reindex(full_index)
        subset.index.name = "open_time"
        subset["symbol"] = symbol

        missing_mask = subset["close"].isna()
        missing += int(missing_mask.sum())
        repaired_close = subset["close"].ffill().bfill().copy()
        jump_mask = pd.Series(False, index=subset.index)
        for position in range(1, len(repaired_close)):
            previous_close = repaired_close.iloc[position - 1]
            current_close = repaired_close.iloc[position]
            if abs(current_close / previous_close - 1.0) > jump_threshold:
                repaired_close.iloc[position] = previous_close
                jump_mask.iloc[position] = True
        jumps += int(jump_mask.sum())
        subset["close"] = repaired_close
        repaired = missing_mask | jump_mask

        subset["open"] = subset["open"].fillna(subset["close"])
        subset["high"] = subset["high"].fillna(subset[["open", "close"]].max(axis=1))
        subset["low"] = subset["low"].fillna(subset[["open", "close"]].min(axis=1))
        subset["high"] = subset[["open", "close", "high"]].max(axis=1)
        subset["low"] = subset[["open", "close", "low"]].min(axis=1)
        subset["volume"] = subset["volume"].fillna(0.0)
        subset["close_time"] = subset.index + pd.to_timedelta(21_599, unit="s")
        subset["repaired"] = repaired
        cleaned_frames.append(subset.reset_index())

    cleaned = pd.concat(cleaned_frames, ignore_index=True)[
        [
            "open_time",
            "close_time",
            "symbol",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "repaired",
        ]
    ]
    validate_market_data(cleaned, symbols=symbols, start=start, end=end, strict_grid=True)
    return cleaned, CleaningSummary(
        duplicate_bars_removed=duplicates,
        missing_bars_repaired=missing,
        jump_bars_repaired=jumps,
    )


def align_risk_free(
    risk_free_daily: pd.DataFrame,
    *,
    start: str,
    end: str,
    bars_per_day: int = 4,
) -> pd.DataFrame:
    """Forward-fill only past or same-date daily observations onto the 6h grid."""
    validate_risk_free_data(risk_free_daily)
    grid = pd.DataFrame(
        {
            "open_time": pd.date_range(
                pd.Timestamp(start, tz="UTC"),
                pd.Timestamp(end, tz="UTC"),
                inclusive="left",
                freq="6h",
            )
        }
    )
    source = risk_free_daily.sort_values("date").copy()
    source["rf_step"] = (source["dff_percent"] / 100.0) / (365 * bars_per_day)
    aligned = pd.merge_asof(
        grid.sort_values("open_time"),
        source.rename(columns={"date": "source_date"}),
        left_on="open_time",
        right_on="source_date",
        direction="backward",
        allow_exact_matches=True,
    )
    if aligned[["dff_percent", "rf_step"]].isna().any().any():
        raise ValueError(
            "Risk-free series does not cover the start of the market sample; "
            "include an observation at or before the start date."
        )
    return aligned[["open_time", "source_date", "dff_percent", "rf_step"]]


def prepare_market_returns(
    market_clean: pd.DataFrame,
    risk_free_aligned: pd.DataFrame,
) -> pd.DataFrame:
    """Compute simple and lagged-risk-free excess returns without future information."""
    returns = market_clean.merge(risk_free_aligned, on="open_time", how="left")
    returns = returns.sort_values(["symbol", "open_time"]).copy()
    returns["simple_return"] = returns.groupby("symbol")["close"].pct_change()
    returns["rf_lag"] = returns.groupby("symbol")["rf_step"].shift(1)
    returns["excess_simple_return"] = returns["simple_return"] - returns["rf_lag"]
    return returns
