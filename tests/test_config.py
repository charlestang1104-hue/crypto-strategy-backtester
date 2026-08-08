from pathlib import Path

import pytest

from crypto_backtester.config import ConfigError, load_config


def test_loads_public_baseline_configuration() -> None:
    config = load_config(Path("configs/full_sample_baseline.yaml"))
    assert config.data.symbols == ("BTCUSDT", "ETHUSDT", "BNBUSDT")
    assert config.strategies.trend_following.fast_window == 8
    assert config.costs == {"low": 0.5, "baseline": 1.0, "high": 1.5}


def test_rejects_unknown_fields(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text("name: test\nunknown: true\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="Unknown configuration"):
        load_config(path)
