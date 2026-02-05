#!/bin/bash
set -e

echo "Running Ruff Format Check..."
uv run ruff format --check adcp_recorder/

echo "Running Ruff Lint Check..."
uv run ruff check adcp_recorder/

echo "Running Mypy Check..."
uv run mypy adcp_recorder/ --check-untyped-defs

echo "Running Tests and Coverage..."
uv run pytest --cov=adcp_recorder --cov-fail-under=100 adcp_recorder/tests/

echo "All checks passed!"
