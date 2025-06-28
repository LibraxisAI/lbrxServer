#!/bin/bash
# Quick test runner

echo "🔍 Running Ruff linting checks..."
uv run ruff check . --fix

echo ""
echo "📊 Running format checks..."
uv run ruff format . --check

echo ""
echo "🧪 Running server tests..."
uv run scripts/testing/test_server.py

echo ""
echo "✅ All checks completed!"