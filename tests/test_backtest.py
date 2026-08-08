import pandas as pd

from crypto_backtester.backtest import simulate_strategy


def _run(cost: float) -> pd.DataFrame:
    index = pd.date_range("2024-01-01", periods=5, freq="6h", tz="UTC")
    targets = pd.DataFrame({"asset": [100.0, -100.0, 100.0, -100.0, 100.0]}, index=index)
    returns = pd.DataFrame({"asset": [0.01] * 5}, index=index)
    pnl, _ = simulate_strategy(
        targets,
        returns,
        initial_capital=100.0,
        gross_limit=100.0,
        leverage_limit=1.0,
        proportional_cost=cost,
    )
    return pnl


def test_higher_cost_cannot_improve_this_identical_backtest() -> None:
    assert _run(0.01)["net_value"].iloc[-1] < _run(0.0)["net_value"].iloc[-1]


def test_portfolio_value_never_becomes_negative() -> None:
    index = pd.date_range("2024-01-01", periods=2, freq="6h", tz="UTC")
    targets = pd.DataFrame({"asset": [1_000.0, 1_000.0]}, index=index)
    returns = pd.DataFrame({"asset": [-2.0, -2.0]}, index=index)
    pnl, positions = simulate_strategy(
        targets,
        returns,
        initial_capital=100.0,
        gross_limit=1_000.0,
        leverage_limit=10.0,
        proportional_cost=0.0,
    )
    assert (pnl["net_value"] >= 0).all()
    assert pnl["net_value"].iloc[-1] == 0.0
    assert positions.iloc[-1].abs().sum() == 0.0
