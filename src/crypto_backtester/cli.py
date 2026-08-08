"""Command-line interface for validation and reproducible research runs."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from crypto_backtester.config import ConfigError, load_config
from crypto_backtester.data.download import DataDownloadError
from crypto_backtester.data.validate import DataValidationError
from crypto_backtester.pipeline import PipelineError, run_experiment, validate_cached_data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="crypto-backtester",
        description="Run cost-aware systematic crypto strategy research.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name, help_text in [
        ("reproduce", "Download or reuse data and reproduce an experiment."),
        ("run", "Run an experiment from existing cached data only."),
        ("validate", "Validate existing cached source data without running a backtest."),
    ]:
        command = subparsers.add_parser(name, help=help_text)
        command.add_argument("--config", type=Path, required=True, help="Path to YAML config.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        if args.command == "validate":
            print(json.dumps(validate_cached_data(config), indent=2))
        else:
            output = run_experiment(config, allow_download=args.command == "reproduce")
            print(f"Experiment complete: {output}")
    except (ConfigError, DataDownloadError, DataValidationError, PipelineError, ValueError) as exc:
        print(f"crypto-backtester: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
