"""Fixed-rule strategy implementations."""

from crypto_backtester.strategies.mean_reversion import build_mean_reversion
from crypto_backtester.strategies.trend_following import build_trend_following

__all__ = ["build_mean_reversion", "build_trend_following"]
