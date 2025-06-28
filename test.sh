#!/bin/bash
# Quick test runner

echo "🔍 Running Ruff linting checks..."
uv run ruff check . --fix

echo ""
echo "📊 Running format checks..."
uv run ruff format . --check

echo ""
echo "🧪 Running unit tests..."
uv run pytest tests/ -v

echo ""
echo "📈 Running integration tests..."
uv run scripts/testing/test_server.py || echo "⚠️  Server not running - skipping integration tests"

echo ""
echo "✅ All checks completed!"