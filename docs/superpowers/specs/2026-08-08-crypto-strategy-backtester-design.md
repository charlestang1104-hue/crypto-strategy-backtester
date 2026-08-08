# Crypto Strategy Backtester Repository Design

Date: 2026-08-08  
Status: Approved on 2026-08-08

## 1. Objective

Convert the existing algorithmic-trading source notebook into a polished, public, research-grade GitHub repository named `crypto-strategy-backtester`.

The primary audience is recruiters and hiring managers for quantitative research and systematic-trading roles. A secondary audience is technical reviewers evaluating data engineering, testing, and software quality.

The repository must preserve the original project files outside the new repository. It must not modify or overwrite the source notebook, source data, figures, or PDF report under `Algorithm trading/`.

## 2. Positioning

The repository is a reproducible research and backtesting framework, not a live-trading system and not evidence of an investable strategy.

The public narrative will emphasize:

- correct time alignment and explicit anti-lookahead safeguards;
- cost-aware backtesting and turnover measurement;
- reproducible data acquisition and experiment configuration;
- transparent reporting of both successful and failed strategies;
- risk metrics and limitations alongside returns;
- modular Python code, tests, command-line usage, and CI.

The public repository will not emphasize course codes, marks, student identifiers, local machine paths, or exaggerated performance claims.

## 3. Goals and Non-goals

### Goals

- Reproduce the existing BTCUSDT, ETHUSDT, and BNBUSDT six-hour-bar analysis for 2024-01-01 through 2026-01-01.
- Implement mean-reversion and trend-following strategies as independently testable modules.
- Reproduce the existing full-sample baseline results within documented numeric tolerances.
- Add a chronological holdout view and multi-scenario transaction-cost analysis.
- Provide a concise research notebook that calls package functions instead of containing the core implementation.
- Provide an English README that communicates value, methodology, results, risks, and reproducibility within one page of initial scrolling.
- Pass linting and automated tests in a clean Python environment.

### Non-goals

- Live order execution, exchange credentials, portfolio brokerage integration, or real-time streaming.
- A hosted web dashboard or Streamlit application.
- Automated parameter optimization over the holdout period.
- Claims of statistical significance, production readiness, or future profitability.
- Committing downloaded bulk raw/intermediate data to Git.

## 4. User-facing Workflows

### Recruiter workflow

1. Open `README.md`.
2. Understand the research question, assets, sample period, and methods from the first screen.
3. Inspect the real equity-curve figure and a balanced metric summary containing both return and drawdown.
4. Review methodology, reproducibility, tests, and limitations without needing to run the project.

### Researcher workflow

1. Create a Python environment and install the project.
2. Run the full-sample baseline configuration.
3. Inspect generated metrics, figures, and the research walkthrough notebook.
4. Run the holdout configuration or change strategy/cost parameters in a copied configuration file.

### Code-review workflow

1. Inspect package boundaries under `src/crypto_backtester/`.
2. Inspect unit, integration, and regression tests.
3. Review CI configuration and command-line entry points.
4. Confirm that notebook cells delegate to tested package functions.

## 5. Repository Structure

```text
crypto-strategy-backtester/
├── README.md
├── LICENSE
├── CITATION.cff
├── pyproject.toml
├── Makefile
├── .gitignore
├── .github/
│   └── workflows/
│       └── ci.yml
├── configs/
│   ├── full_sample_baseline.yaml
│   └── holdout_evaluation.yaml
├── src/
│   └── crypto_backtester/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       ├── config.py
│       ├── pipeline.py
│       ├── features.py
│       ├── costs.py
│       ├── backtest.py
│       ├── metrics.py
│       ├── plotting.py
│       ├── data/
│       │   ├── __init__.py
│       │   ├── download.py
│       │   ├── validate.py
│       │   └── clean.py
│       └── strategies/
│           ├── __init__.py
│           ├── mean_reversion.py
│           └── trend_following.py
├── notebooks/
│   └── research_walkthrough.ipynb
├── tests/
│   ├── fixtures/
│   ├── test_data.py
│   ├── test_features.py
│   ├── test_strategies.py
│   ├── test_costs.py
│   ├── test_backtest.py
│   ├── test_metrics.py
│   ├── test_pipeline.py
│   └── test_cli.py
├── artifacts/
│   ├── full_sample_baseline/
│   │   ├── metrics/
│   │   └── figures/
│   └── holdout_evaluation/
│       ├── metrics/
│       └── figures/
├── data/
│   └── README.md
└── docs/
    ├── methodology.md
    ├── limitations.md
    ├── research-report.pdf
    └── superpowers/specs/
        └── 2026-08-08-crypto-strategy-backtester-design.md
```

## 6. Component Boundaries

### Configuration

`config.py` loads and validates YAML experiment configuration. It returns typed configuration objects and rejects unknown or invalid fields. Configuration covers assets, dates, bar interval, strategy parameters, capital, exposure cap, cost scenarios, output paths, and evaluation periods.

### Data acquisition

`data/download.py` downloads Binance Vision monthly archives and the FRED daily federal-funds series. It provides bounded retries, timeouts, cache reuse, and clear failure messages. Downloaded files are written only under ignored local data directories.

### Data validation and cleaning

`data/validate.py` checks required columns, symbol coverage, UTC timestamps, monotonic ordering, duplicate bars, expected six-hour spacing, numeric validity, and positive prices.

`data/clean.py` removes duplicates, restores the six-hour grid, applies the documented outlier-repair rule, aligns the risk-free proxy, and produces analysis-ready returns. Cleaning produces a structured validation summary rather than silently discarding anomalies.

### Features and strategies

`features.py` contains reusable rolling transformations. Strategy modules receive price/return panels and return target positions. Every strategy applies a one-bar lag between signal observation and executable position.

`mean_reversion.py` implements the rolling z-score rule. `trend_following.py` implements fast/slow moving-average direction. Position normalization enforces the configured gross-exposure cap.

### Costs and backtest

`costs.py` implements the Roll-style estimator and configurable fee/slippage scenarios. Cost settings are explicit inputs to the backtest.

`backtest.py` applies capital-aware exposure scaling, position drift, turnover, gross PnL, trading costs, net PnL, and non-negative portfolio-value constraints. It never mutates input frames.

### Metrics and plotting

`metrics.py` calculates return, turnover, holding-period, Sharpe, Sortino, Calmar, and maximum drawdown with documented six-hour annualization conventions.

`plotting.py` creates deterministic, publication-quality figures from result frames. Figure generation is separate from strategy/backtest logic.

### Pipeline and CLI

`pipeline.py` orchestrates download, validation, cleaning, signal construction, backtesting, metrics, and artifact writing.

`cli.py` exposes a console command named `crypto-backtester`. The primary command is:

```bash
crypto-backtester reproduce --config configs/full_sample_baseline.yaml
```

Additional commands will validate cached data and run a configured experiment. CLI failures return non-zero exit codes.

## 7. Data Flow

```text
Binance Vision + FRED
        ↓
download cache
        ↓
schema/time-grid validation
        ↓
clean prices + aligned risk-free rate + excess returns
        ↓
rolling features
        ↓
one-bar-lagged target positions
        ↓
capital-aware execution + turnover + costs
        ↓
PnL frames + metrics + figures
        ↓
atomic artifact publication
```

All timestamps are UTC. Raw observations are never overwritten. Derived datasets and artifacts include configuration metadata sufficient to identify the experiment that produced them.

## 8. Experiment Designs

### Full-sample baseline

`full_sample_baseline.yaml` reproduces the original fixed rules over 2024-01-01 through 2026-01-01:

- Assets: BTCUSDT, ETHUSDT, BNBUSDT.
- Interval: six-hour bars.
- Initial capital: 10,000 USDT.
- Gross signal exposure cap: 100,000 USDT.
- Mean reversion: 40-bar rolling z-score using the existing threshold logic.
- Trend following: 8-bar fast and 32-bar slow moving averages.
- Execution: positions lagged one bar.
- Cost baseline: mean per-asset Roll-style slippage estimate.

Existing metrics and figures are used as regression references, subject to explicit tolerances for floating-point and dependency-version differences.

### Holdout evaluation

`holdout_evaluation.yaml` reports the same fixed rules separately for:

- Development view: 2024-01-01 through 2025-01-01.
- Holdout view: 2025-01-01 through 2026-01-01.

The holdout period is not used to optimize strategy parameters. The README will still disclose that the repository was constructed retrospectively from an existing full-sample analysis, so this holdout is illustrative rather than a pristine deployment-grade out-of-sample test.

### Cost scenarios

Both experiments report low, baseline, and high cost settings. The configuration records every fee and slippage assumption. Results must show gross and net performance together.

## 9. Public Data Policy

The Git repository includes:

- generated baseline and holdout metric tables;
- the four principal baseline figures plus holdout/cost-sensitivity figures;
- a small synthetic or reduced test fixture;
- data-source documentation and field definitions;
- the authored research report.

The Git repository excludes:

- downloaded raw archives;
- full raw, clean, and intermediate datasets;
- large strategy-position and per-bar PnL exports;
- local virtual environments, caches, notebook checkpoints, and operating-system metadata.

The download pipeline records source URLs and retrieval metadata. Data-source attribution appears in both `data/README.md` and the main README.

## 10. Error Handling and Artifact Safety

- Network requests use explicit timeouts and bounded retries.
- Cached source files allow offline reruns after a successful download.
- Invalid archives, missing columns, timestamp gaps, duplicates, non-positive prices, or non-finite values produce actionable validation errors.
- The pipeline does not silently continue after a failed validation.
- User-facing errors include the failing stage and remediation guidance without exposing local secrets.
- Artifacts are first produced in a temporary run directory. The final artifact directory is replaced only after every required output succeeds.
- Existing artifacts remain intact after a failed run.

## 11. Testing and Continuous Integration

### Unit tests

Tests must verify:

- a signal observed at bar `t` cannot affect executed position at bar `t`;
- gross exposure never exceeds the configured cap;
- capital-aware scaling prevents portfolio value from becoming negative;
- increasing otherwise identical transaction costs cannot improve net PnL;
- data cleaning handles duplicates, gaps, and the documented outlier rule;
- risk-free alignment uses only available information;
- Sharpe, Sortino, Calmar, drawdown, turnover, and holding-period calculations match hand-checked fixtures;
- invalid configurations and malformed data fail clearly.

### Integration and regression tests

- A small synthetic market fixture runs through the complete pipeline without network access.
- The CLI produces the expected directory structure and exit codes.
- A fixed fixture protects selected result columns against unintended changes within documented tolerances.

### CI

GitHub Actions runs on Python 3.11 and 3.12. It installs the package from `pyproject.toml`, runs Ruff checks, and executes pytest with no internet dependency. Full historical-data reproduction is a documented local workflow, not a CI requirement.

## 12. README and Visual Design

The README is written in English and uses a restrained, white-background, research-report style.

The first screen contains:

- `Crypto Strategy Backtester` title;
- a one-sentence, cost-aware research description;
- Python, CI, test, and license badges;
- a real baseline equity/PnL figure;
- asset/sample-size cards;
- Sharpe and maximum-drawdown cards shown together;
- a research and non-investment disclaimer.

The remaining section order is:

1. Why this project.
2. Methodology and anti-lookahead design.
3. Three-command reproduction.
4. Full-sample baseline and holdout results.
5. Cost sensitivity and risk.
6. Architecture and tests.
7. Limitations and next research steps.
8. Data attribution, citation, and license.

The README will not hide the failed mean-reversion result or use the trend-following return without adjacent risk context.

## 13. Packaging, Commands, and Dependencies

The package uses a `src` layout and a `pyproject.toml` build configuration. Runtime dependencies are limited to libraries required by the analysis, including NumPy, pandas, Matplotlib, Requests, PyArrow, and PyYAML. Development dependencies include pytest and Ruff.

Documented commands are:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
make test
make reproduce
```

The Makefile delegates to package/CLI commands; it does not contain business logic.

## 14. Privacy, Security, Attribution, and Licensing

- No credentials, tokens, email passwords, personal identifiers, or local absolute paths may be committed.
- The repository includes secret-oriented ignore patterns and is scanned before delivery.
- The public README omits course codes, assessment language, and student identifiers.
- The author name may appear in `CITATION.cff` and the research report.
- Source data is attributed to Binance Vision and the Federal Reserve data source used by the pipeline.
- The authored code is released under the MIT License. Third-party data and libraries remain under their own terms.
- The repository must not imply endorsement by the university, Binance, or the Federal Reserve.

## 15. Source Migration

Implementation will copy or transform selected material from the source project without changing the source:

- extract reusable logic from `Algorithm Trading.ipynb` into package modules;
- create a new, concise `research_walkthrough.ipynb` that imports the package;
- copy verified baseline figures and metrics as initial regression references;
- copy the authored report to `docs/research-report.pdf`;
- remove notebook metadata, local paths, and course-specific wording from the public surface;
- keep the original `Algorithm trading/` directory untouched.

## 16. Acceptance Criteria

The repository is ready for GitHub when all of the following are true:

1. A clean Python 3.11 or 3.12 environment can install the package from the documented command.
2. `make test` passes locally and the CI workflow is valid.
3. `make reproduce` downloads or reuses cached data and regenerates the required tables and figures.
4. Baseline regression outputs match the accepted references within documented tolerances.
5. Holdout and cost-scenario outputs are present and clearly labeled.
6. README numbers match committed artifact files.
7. README includes real visuals, reproducibility commands, risk disclosure, limitations, data attribution, and licensing.
8. The repository contains no secrets, personal identifiers, local absolute paths, virtual environment, cache, or project brief.
9. The source project directory has no changes.
10. Git history contains the approved design, implementation, and final verification commits.
