# Data sources and local cache

The repository intentionally does **not** commit downloaded market or macroeconomic data. The
`reproduce` command creates a local, ignored cache under `data/cache/`.

## Sources

| Dataset | Public source | Fields used | Frequency |
|---|---|---|---|
| Spot klines | [Binance Public Data](https://data.binance.vision/) | UTC time, OHLC, volume | 6 hours |
| Effective Federal Funds Rate (DFF) | [FRED](https://fred.stlouisfed.org/series/DFF) | Date, annual percent rate | Daily |

The default experiment uses BTCUSDT, ETHUSDT, and BNBUSDT from 2024-01-01 (inclusive) to
2026-01-01 (exclusive). Each asset contributes 2,924 bars before feature warm-up.

## Cache layout

After a successful download:

```text
data/cache/
├── market_raw_6h.csv
├── risk_free_daily.csv
└── retrieval_metadata.json
```

The metadata file records the public URLs, requested sample, and retrieval timestamp. Downloads
use timeouts, bounded retries, and atomic file replacement. Existing cache files are reused.

## Validation and cleaning

Before research code runs, the pipeline checks:

- required columns and configured symbol coverage;
- timezone-aware UTC timestamps and chronological ordering;
- duplicate and missing 6-hour bars;
- finite numeric values, positive OHLC prices, and non-negative volume;
- daily risk-free coverage without backward-filling future observations.

Duplicates are removed, a complete 6-hour grid is restored, and missing prices are documented as
repairs. A close-to-close move above 20% is replaced sequentially with the last accepted close, which
prevents a single bad print from contaminating the next comparison. Repair counts are written to each
experiment's `validation_summary.json`.

## Licensing

The MIT license in this repository covers the authored source code only. Binance and FRED data remain
subject to their respective terms. This project is not affiliated with or endorsed by Binance, the
Federal Reserve Bank of St. Louis, or any university.
