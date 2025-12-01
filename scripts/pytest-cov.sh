#!/bin/bash

# Run pytest with coverage
uv run pytest --cov --cov-branch

# Generate coverage report
uv run coverage html