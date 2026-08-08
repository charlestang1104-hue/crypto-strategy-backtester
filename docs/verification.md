# Final verification record

Date: 2026-08-08
Implementation commit: `0bfbd4b`

## Environment

- macOS ARM64
- Python 3.12.13 in a clean project-local virtual environment
- Package installed from `pyproject.toml` with `python -m pip install -e ".[dev]"`

## Quality gates

| Check | Command | Result |
|---|---|---|
| Lint | `python -m ruff check .` | Passed |
| Format | `python -m ruff format --check .` | 35 files formatted |
| Tests | `python -m pytest --cov=crypto_backtester --cov-report=term-missing` | 19 passed |
| Coverage | Same pytest run | 81% total |
| Wheel build | `python -m pip wheel . --no-deps` | Built `crypto_strategy_backtester-1.0.0-py3-none-any.whl` |
| README links | Local-link existence scan | 15 checked; none missing |
| Notebook | JSON validation | Valid nbformat 4 document |
| Git whitespace | `git diff --check` | Passed; PDF/PNG declared binary |

Tests include unit checks for anti-lookahead timing, exposure limits, cleaning, risk-free alignment,
transaction costs, capital constraints, and metrics; a network-free synthetic integration run; CLI
success/failure behavior; and accepted full-sample regression values.

## Data and experiment verification

- Cached real source data validated: 8,772 rows, 3 configured symbols, 0 duplicate bars, 0 missing
  grid bars, 0 non-positive prices, and 0 non-finite values.
- `crypto-backtester run --config configs/full_sample_baseline.yaml` completed successfully.
- `crypto-backtester run --config configs/holdout_evaluation.yaml` completed successfully.
- The cache-reuse path was used for the real-data run. The synthetic integration test explicitly
  prevents network data access.
- Artifacts were regenerated from the modular package after final code changes.

Selected baseline regression values:

| Strategy | Net return | Sharpe | Sortino | Max drawdown |
|---|---:|---:|---:|---:|
| Mean reversion | -100.00% | -0.6796 | -0.2642 | -100.00% |
| Trend following | +188.99% | 0.2066 | 0.2765 | -82.10% |

Selected chronological result:

| Period | Strategy | Net return | Sharpe | Max drawdown |
|---|---|---:|---:|---:|
| Development 2024 | Trend following | +280.69% | 0.6042 | -74.84% |
| Illustrative holdout 2025 | Trend following | -100.00% | -1.4464 | -100.00% |

## PDF and public-surface QA

- `docs/research-report.pdf` was rebuilt from committed artifacts.
- Poppler identified a five-page, unencrypted A4 PDF with no JavaScript or forms.
- All five pages were rendered to PNG and visually inspected for clipping, overlap, broken tables,
  unreadable charts, headers, footers, and page numbers. No layout defects were found.
- Repository scans found no committed local absolute paths, credentials, student numbers, module
  codes, or course-specific public naming.
- The original notebook and original report outside this repository were read and copied from only;
  no commands wrote to the source project directory.

## Artifact checksums

```text
d88216b1b98a840b24e82973c9f7798cd1041196dad407f8e1a857c9f8df998c  docs/research-report.pdf
1cf2e44906f59d724c7ad08f33e8d168ddea5140cb8a17d3a141fc44c9a7d31a  artifacts/full_sample_baseline/metrics/performance_summary.csv
7ab987f1e0c71d4f9c686daac3b8bf3963d5d6e0409fcad2bf0b0e81b8d2f3c3  artifacts/holdout_evaluation/metrics/performance_summary.csv
```
