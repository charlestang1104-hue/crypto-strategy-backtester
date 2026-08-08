import numpy as np
import pandas as pd

from crypto_backtester.metrics import average_holding_days, calculate_metrics, max_drawdown


def test_drawdown_matches_hand_calculation() -> None:
    assert np.isclose(max_drawdown(pd.Series([100.0, 110.0, 88.0, 99.0])), -0.2)


def test_average_holding_period_matches_sign_runs() -> None:
    positions = pd.DataFrame({"asset": [1, 1, 0, -1, -1, -1, 0]})
    assert np.isclose(average_holding_days(positions), (2 + 3) / 2 * 6 / 24)


def test_metrics_preserve_accounting_identity() -> None:
    pnl = pd.DataFrame(
        {
            "gross_pnl": [10.0, -5.0],
            "net_pnl": [9.0, -6.0],
            "turnover": [100.0, 100.0],
            "cost": [1.0, 1.0],
            "net_value": [109.0, 103.0],
            "gross_value": [110.0, 105.0],
        }
    )
    positions = pd.DataFrame({"asset": [100.0, -100.0]})
    metrics = calculate_metrics(pnl, positions, initial_capital=100.0)
    assert metrics["net_pnl_usdt"] == 3.0
    assert np.isclose(metrics["net_return"], 0.03)
    assert metrics["total_cost_usdt"] == 2.0
