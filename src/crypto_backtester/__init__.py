"""Cost-aware research backtester for systematic crypto strategies."""

__version__ = "1.0.0"

from crypto_backtester.config import ExperimentConfig, load_config


def run_experiment(*args: object, **kwargs: object):  # type: ignore[no-untyped-def]
    """Lazily import the plotting-heavy experiment pipeline."""
    from crypto_backtester.pipeline import run_experiment as _run_experiment

    return _run_experiment(*args, **kwargs)


__all__ = ["ExperimentConfig", "load_config", "run_experiment"]
