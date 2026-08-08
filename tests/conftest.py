from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def synthetic_sources(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path
    cache = root / "data" / "cache"
    configs = root / "configs"
    cache.mkdir(parents=True)
    configs.mkdir()

    timestamps = pd.date_range("2024-01-01", periods=80, freq="6h", tz="UTC")
    rows: list[dict[str, object]] = []
    for asset_index, symbol in enumerate(["AAAUSDT", "BBBUSDT"]):
        phase = np.arange(len(timestamps), dtype=float)
        close = 100 + 0.15 * phase + 2.5 * np.sin(phase / (3.0 + asset_index))
        for timestamp, price in zip(timestamps, close, strict=True):
            rows.append(
                {
                    "open_time": timestamp,
                    "close_time": timestamp + pd.to_timedelta(21_599, unit="s"),
                    "symbol": symbol,
                    "open": price * 0.999,
                    "high": price * 1.005,
                    "low": price * 0.995,
                    "close": price,
                    "volume": 1000.0 + asset_index,
                }
            )
    pd.DataFrame(rows).to_csv(cache / "market_raw_6h.csv", index=False)
    days = pd.date_range("2024-01-01", "2024-01-20", freq="D", tz="UTC")
    pd.DataFrame({"date": days, "dff_percent": 5.0}).to_csv(
        cache / "risk_free_daily.csv", index=False
    )
    config_path = configs / "synthetic.yaml"
    config_path.write_text(
        """name: synthetic
data:
  symbols: [AAAUSDT, BBBUSDT]
  interval: 6h
  start: "2024-01-01"
  end: "2024-01-21"
  cache_dir: data/cache
portfolio:
  initial_capital: 10000.0
  gross_limit: 20000.0
  leverage_limit: 2.0
strategies:
  mean_reversion:
    window: 8
    z_threshold: 1.0
  trend_following:
    fast_window: 3
    slow_window: 8
costs:
  low: 0.5
  baseline: 1.0
  high: 1.5
evaluation:
  full_sample:
    start: "2024-01-01"
    end: "2024-01-21"
output_dir: artifacts/synthetic
""",
        encoding="utf-8",
    )
    return root, config_path
