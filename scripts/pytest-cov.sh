#!/bin/bash

# Run pytest with coverage
uv run pytest --cov

# Generate coverage report
uv run coverage html