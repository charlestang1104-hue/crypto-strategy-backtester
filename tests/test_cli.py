from pathlib import Path

from crypto_backtester.cli import main


def test_validate_command_returns_success(synthetic_sources: tuple[Path, Path], capsys) -> None:
    _, config_path = synthetic_sources
    exit_code = main(["validate", "--config", str(config_path)])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert '"missing_grid_bars": 0' in captured.out


def test_missing_config_returns_nonzero(tmp_path: Path, capsys) -> None:
    exit_code = main(["validate", "--config", str(tmp_path / "missing.yaml")])
    captured = capsys.readouterr()
    assert exit_code == 2
    assert "Configuration not found" in captured.err
