from pathlib import Path

import numpy as np
import pandas as pd


def test_committed_baseline_reference_matches_accepted_results() -> None:
    path = Path("artifacts/full_sample_baseline/metrics/performance_summary.csv")
    metrics = pd.read_csv(path)
    baseline = metrics.loc[metrics["cost_scenario"] == "baseline"].set_index("strategy")
    trend = baseline.loc["trend_following"]
    mean_reversion = baseline.loc["mean_reversion"]
    assert np.isclose(trend["net_return"], 1.88988368, atol=1e-6)
    assert np.isclose(trend["sharpe_net"], 0.20657987, atol=1e-6)
    assert np.isclose(trend["max_drawdown_net"], -0.82104222, atol=1e-6)
    assert np.isclose(mean_reversion["net_return"], -1.0, atol=1e-8)
