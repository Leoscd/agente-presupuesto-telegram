.PHONY: install dev test golden lint typecheck clean

install:
	pip install -e ".[dev]"

dev:
	python -m src.bot.main

test:
	pytest -q

golden:
	python -m scripts.correr_golden --strict

lint:
	ruff check src tests scripts
	ruff format --check src tests scripts

format:
	ruff format src tests scripts

typecheck:
	mypy src

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache **/__pycache__ *.egg-info build dist
