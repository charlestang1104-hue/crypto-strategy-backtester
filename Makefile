.PHONY: install lint test reproduce holdout report clean

install:
	python -m pip install -e ".[dev]"

lint:
	python -m ruff check .

test:
	python -m pytest

reproduce:
	python -m crypto_backtester reproduce --config configs/full_sample_baseline.yaml

holdout:
	python -m crypto_backtester reproduce --config configs/holdout_evaluation.yaml

report:
	python scripts/build_report.py

clean:
	python -c "from pathlib import Path; import shutil; [shutil.rmtree(p, ignore_errors=True) for p in [Path('.pytest_cache'), Path('.ruff_cache'), Path('build')]]"
