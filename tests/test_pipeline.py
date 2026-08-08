from pathlib import Path

import pandas as pd

from crypto_backtester.pipeline import run_experiment


def test_synthetic_pipeline_runs_without_network(
    synthetic_sources: tuple[Path, Path],
) -> None:
    root, config_path = synthetic_sources
    output = run_experiment(config_path, allow_download=False)
    assert output == root / "artifacts" / "synthetic"
    metrics_path = output / "metrics" / "performance_summary.csv"
    metrics = pd.read_csv(metrics_path)
    assert len(metrics) == 6
    assert set(metrics["strategy"]) == {"mean_reversion", "trend_following"}
    assert set(metrics["cost_scenario"]) == {"low", "baseline", "high"}
    assert (output / "figures" / "full_sample_equity_curves.png").exists()
    assert (output / "metrics" / "validation_summary.json").exists()
