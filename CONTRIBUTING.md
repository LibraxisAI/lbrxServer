# Contributing to MLX LLM Server

We love your input! We want to make contributing to MLX LLM Server as easy and transparent as possible.

## Development Process

We use GitHub to host code, to track issues and feature requests, as well as accept pull requests.

1. Fork the repo and create your branch from `develop`
2. If you've added code that should be tested, add tests
3. If you've changed APIs, update the documentation
4. Ensure the test suite passes
5. Make sure your code lints
6. Issue that pull request!

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/mlx-llm-server.git
cd mlx-llm-server

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Run development server
./scripts/start_server.sh dev
```

## Code Style

We use `ruff` for linting and formatting:

```bash
# Check linting
uv run ruff check .

# Format code
uv run ruff format .

# Run all checks
./test.sh
```

## Pull Request Process

1. Update the README.md with details of changes if needed
2. Update the docs/ with any new environment variables, ports, or useful file locations
3. The PR will be merged once you have the sign-off of at least one maintainer

## Any contributions you make will be under the MIT Software License

When you submit code changes, your submissions are understood to be under the same [MIT License](LICENSE) that covers the project.

## Report bugs using GitHub's [issue tracker](https://github.com/LibraxisAI/mlx-llm-server/issues)

**Great Bug Reports** tend to have:

- A quick summary and/or background
- Steps to reproduce
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening)

## License

By contributing, you agree that your contributions will be licensed under its MIT License.