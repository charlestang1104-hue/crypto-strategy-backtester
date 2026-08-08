# Methodology

## Research question

Can two transparent fixed-rule signals - rolling z-score mean reversion and moving-average trend
following - survive a simple, turnover-linked transaction-cost model on liquid cryptocurrency pairs?

The project prioritizes reproducibility and failure analysis over strategy novelty. Parameters are
fixed before the development/holdout comparison, and unsuccessful results remain visible.

## Data and return construction

The default sample contains 6-hour BTCUSDT, ETHUSDT, and BNBUSDT spot bars from 2024-01-01 through
2025-12-31 UTC. For asset \(i\), the close-to-close simple return at bar \(t\) is

```text
r[i,t] = close[i,t] / close[i,t-1] - 1.
```

The daily effective federal funds rate is converted to a 6-hour step rate using 365 x 4 periods per
year. Excess-return fields use a one-bar-lagged step rate. Strategy rules use prices directly; the
risk-free series is retained for analysis and future extensions.

## Signals and anti-lookahead timing

Mean reversion uses a 40-bar rolling z-score. A z-score above +1 creates a short signal; one below -1
creates a long signal. Trend following compares 8-bar and 32-bar simple moving averages and takes the
sign of the difference.

Signals observed at bar \(t\) are executable only at bar \(t+1\):

```text
executed_target[t] = normalize(signal[t-1]).
```

This `shift(1)` rule is centralized in `features.target_positions` and protected by a unit test. Gross
target exposure is normalized to at most 100,000 USDT.

## Transaction costs

For each asset, a Roll-style proportional estimate is calculated from lag-1 return covariance:

```text
slippage[i] = sqrt(max(-Cov(r[i,t], r[i,t-1]), 0)).
```

The baseline cost is the equal-weighted mean across assets. Low and high scenarios apply 0.5x and
1.5x multipliers. The model is intentionally simple: it exposes turnover sensitivity but does not
represent a full exchange limit-order book, fee tier, or market-impact curve.

## Portfolio simulation

The simulator begins with 10,000 USDT. At every bar it:

1. drifts the previous position by the previous asset return;
2. scales the new target to the smaller of the 100,000 USDT cap and 10x current equity;
3. calculates turnover from the drifted position to the new executed position;
4. deducts proportional cost from gross PnL;
5. clips realized loss at remaining capital and stops exposure after bankruptcy.

The simulator returns gross PnL, raw and realized net PnL, cost, turnover, gross value, net value, and
executed positions. Inputs are never mutated.

## Metrics

Sharpe and Sortino ratios annualize 6-hour PnL returns with \(4 x 365 = 1,460\) bars per year. The
repository also reports final value, net return on initial capital, maximum drawdown, Calmar ratio,
turnover, total modeled cost, and average same-sign holding duration.

## Evaluation design

- **Full sample:** 2024-01-01 to 2026-01-01, used to reproduce the original fixed-rule baseline.
- **Development:** 2024-01-01 to 2025-01-01.
- **Illustrative holdout:** 2025-01-01 to 2026-01-01.

The holdout is not pristine: this repository was constructed retrospectively from an earlier
full-sample analysis. No parameter tuning is performed on the holdout, but the result should be read as
a robustness demonstration, not a deployment-grade out-of-sample claim.
