import numpy as np
import pandas as pd

from crypto_backtester.costs import cost_scenarios, roll_slippage_estimates


def test_roll_estimator_truncates_positive_covariance() -> None:
    returns = pd.DataFrame(
        {
            "symbol": ["A"] * 5 + ["B"] * 5,
            "simple_return": [0.01, -0.01, 0.01, -0.01, 0.01, 0.01, 0.02, 0.03, 0.04, 0.05],
        }
    )
    estimates = roll_slippage_estimates(returns).set_index("symbol")
    assert estimates.loc["A", "roll_slippage"] > 0
    assert estimates.loc["B", "roll_slippage"] == 0


def test_named_cost_scenarios_scale_the_same_base() -> None:
    estimates = pd.DataFrame({"roll_slippage": [0.001, 0.003]})
    scenarios = cost_scenarios(estimates, {"low": 0.5, "baseline": 1.0, "high": 1.5})
    assert np.isclose(scenarios["low"], 0.001)
    assert np.isclose(scenarios["baseline"], 0.002)
    assert np.isclose(scenarios["high"], 0.003)
