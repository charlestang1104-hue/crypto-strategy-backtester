"""Download and cache public Binance Vision and FRED source data."""

from __future__ import annotations

import io
import json
import time
import zipfile
from pathlib import Path

import pandas as pd
import requests

from crypto_backtester.config import DataConfig

KLINE_COLUMNS = [
    "open_time",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "close_time",
    "quote_asset_volume",
    "number_of_trades",
    "taker_buy_base_volume",
    "taker_buy_quote_volume",
    "ignore",
]


class DataDownloadError(RuntimeError):
    """Raised when a public source cannot be downloaded or decoded."""


def month_starts(start: str, end: str) -> pd.DatetimeIndex:
    first = pd.Timestamp(start).to_period("M").to_timestamp()
    last = (pd.Timestamp(end) - pd.Timedelta(days=1)).to_period("M").to_timestamp()
    return pd.date_range(first, last, freq="MS")


def parse_binance_timestamp(series: pd.Series) -> pd.Series:
    """Parse both millisecond and post-2025 microsecond Binance timestamps."""
    values = pd.to_numeric(series, errors="coerce")
    result = pd.Series(pd.NaT, index=series.index, dtype="datetime64[ns, UTC]")
    milliseconds = values.notna() & (values < 10**14)
    microseconds = values.notna() & (values >= 10**14)
    if milliseconds.any():
        result.loc[milliseconds] = pd.to_datetime(
            values.loc[milliseconds].astype("int64"), unit="ms", utc=True, errors="coerce"
        )
    if microseconds.any():
        result.loc[microseconds] = pd.to_datetime(
            values.loc[microseconds].astype("int64"), unit="us", utc=True, errors="coerce"
        )
    return result


def _get_with_retries(
    session: requests.Session,
    url: str,
    *,
    timeout: float = 60,
    attempts: int = 3,
) -> requests.Response:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            response = session.get(url, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            last_error = exc
            if attempt < attempts:
                time.sleep(0.5 * attempt)
    raise DataDownloadError(
        f"Download failed after {attempts} attempts: {url}. "
        "Check network access or populate data/cache manually."
    ) from last_error


def _atomic_csv(frame: pd.DataFrame, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    frame.to_csv(temporary, index=False)
    temporary.replace(destination)


def _download_symbol(
    session: requests.Session,
    symbol: str,
    config: DataConfig,
    source_urls: list[str],
) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for month in month_starts(config.start, config.end):
        month_code = month.strftime("%Y-%m")
        url = (
            "https://data.binance.vision/data/spot/monthly/klines/"
            f"{symbol}/{config.interval}/{symbol}-{config.interval}-{month_code}.zip"
        )
        response = _get_with_retries(session, url)
        source_urls.append(url)
        try:
            with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
                members = archive.namelist()
                if len(members) != 1:
                    raise DataDownloadError(f"Unexpected archive contents for {url}")
                with archive.open(members[0]) as stream:
                    frames.append(pd.read_csv(stream, header=None, names=KLINE_COLUMNS))
        except (zipfile.BadZipFile, OSError, ValueError) as exc:
            raise DataDownloadError(f"Invalid Binance archive: {url}") from exc

    market = pd.concat(frames, ignore_index=True)
    market["open_time"] = parse_binance_timestamp(market["open_time"])
    market["close_time"] = parse_binance_timestamp(market["close_time"])
    for column in ["open", "high", "low", "close", "volume"]:
        market[column] = pd.to_numeric(market[column], errors="coerce")
    start = pd.Timestamp(config.start, tz="UTC")
    end = pd.Timestamp(config.end, tz="UTC")
    market = market[(market["open_time"] >= start) & (market["open_time"] < end)].copy()
    market["symbol"] = symbol
    return market[["open_time", "close_time", "symbol", "open", "high", "low", "close", "volume"]]


def download_sources(config: DataConfig) -> tuple[Path, Path]:
    """Download all configured market bars and the daily risk-free proxy."""
    session = requests.Session()
    session.headers.update({"User-Agent": "crypto-strategy-backtester/1.0"})
    urls: list[str] = []
    frames = [_download_symbol(session, symbol, config, urls) for symbol in config.symbols]
    market = pd.concat(frames, ignore_index=True)

    fred_url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFF"
    fred_response = _get_with_retries(session, fred_url)
    urls.append(fred_url)
    risk_free = pd.read_csv(io.BytesIO(fred_response.content))
    risk_free = risk_free.rename(columns={"observation_date": "date", "DFF": "dff_percent"})
    if not {"date", "dff_percent"}.issubset(risk_free.columns):
        raise DataDownloadError("FRED response is missing date or DFF columns")
    risk_free["date"] = pd.to_datetime(risk_free["date"], utc=True, errors="coerce")
    risk_free["dff_percent"] = pd.to_numeric(risk_free["dff_percent"], errors="coerce")
    risk_free = risk_free.dropna().copy()
    start = pd.Timestamp(config.start, tz="UTC")
    end = pd.Timestamp(config.end, tz="UTC")
    risk_free = risk_free[
        (risk_free["date"] >= start - pd.Timedelta(days=7)) & (risk_free["date"] < end)
    ]

    market_path = config.cache_dir / "market_raw_6h.csv"
    risk_free_path = config.cache_dir / "risk_free_daily.csv"
    _atomic_csv(market, market_path)
    _atomic_csv(risk_free, risk_free_path)
    metadata = {
        "sources": urls,
        "symbols": list(config.symbols),
        "interval": config.interval,
        "start": config.start,
        "end": config.end,
        "retrieved_at_utc": pd.Timestamp.now(tz="UTC").isoformat(),
    }
    metadata_path = config.cache_dir / "retrieval_metadata.json"
    temporary = metadata_path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    temporary.replace(metadata_path)
    return market_path, risk_free_path


def ensure_cached_sources(config: DataConfig, *, allow_download: bool) -> tuple[Path, Path]:
    """Reuse validated source filenames, or download them when explicitly allowed."""
    market_path = config.cache_dir / "market_raw_6h.csv"
    risk_free_path = config.cache_dir / "risk_free_daily.csv"
    if market_path.exists() and risk_free_path.exists():
        return market_path, risk_free_path
    if not allow_download:
        raise DataDownloadError(
            f"Cached data not found under {config.cache_dir}. "
            "Run the reproduce command with network access first."
        )
    return download_sources(config)
