# Limitations and next research steps

## What the results do not prove

- The experiment covers three crypto assets and one two-year market regime.
- The full-sample trend result has a low Sharpe ratio and an 82% maximum drawdown.
- Both strategies lose almost all capital in the illustrative 2025 holdout at baseline costs.
- The holdout is retrospective and is not a pristine live or paper-trading record.
- No statistical-significance, multiple-testing, or parameter-stability claim is made.

## Execution model limitations

The Roll-style estimator is a deliberately compact turnover penalty. It omits exchange fees, bid-ask
spread dynamics, nonlinear market impact, funding, latency, partial fills, delistings, and liquidity
constraints. Target positions assume synchronous 6-hour bars and immediate rebalancing at the modeled
return boundary.

## Data limitations

The cleaning rule repairs missing bars and close moves above 20%. This is suitable for demonstrating a
defensive pipeline, but a production research system should compare multiple vendors, retain exchange
status events, and investigate every repair rather than treating a fixed threshold as ground truth.

## Sensible next steps

1. Add volatility-targeted sizing and portfolio-level risk budgets.
2. Estimate spread and market impact from higher-frequency quote/trade data.
3. Use rolling or expanding walk-forward evaluation with pre-registered parameters.
4. Add bootstrap uncertainty intervals and multiple-testing controls.
5. Expand the asset universe while controlling survivorship and listing-date bias.
6. Run a forward paper-trading period before considering any live deployment.
