"""Data acquisition, validation, and cleaning utilities."""

from crypto_backtester.data.clean import clean_market_data, prepare_market_returns
from crypto_backtester.data.download import ensure_cached_sources
from crypto_backtester.data.validate import DataValidationError, validate_market_data

__all__ = [
    "DataValidationError",
    "clean_market_data",
    "ensure_cached_sources",
    "prepare_market_returns",
    "validate_market_data",
]
