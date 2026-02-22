# Contributing

We welcome contributions of all kinds: bug fixes, new adapters, scoring
improvements, documentation, and more.

## Getting Started

1. Fork the repository and clone your fork.
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -e ".[dev]"
   ```
3. Run the tests to make sure everything works:
   ```bash
   make test
   ```

## Development Workflow

1. Create a branch: `git checkout -b feature/my-feature`
2. Make your changes.
3. Run linting and tests:
   ```bash
   make lint
   make test
   ```
4. Commit with a descriptive message.
5. Push and open a Pull Request.

## Adding a New Retailer Adapter

See the cookbook guide: [How to Add a New Retailer Adapter](cookbook/04-add-retailer-adapter.md).

In short:
1. Create `src/adapters/your_store_adapter.py`.
2. Implement the `BaseAdapter` interface.
3. Register it in `src/adapters/__init__.py`.
4. Add tests in `tests/test_your_store_adapter.py`.

## Code Style

* We use [Ruff](https://github.com/astral-sh/ruff) for linting and formatting.
* Keep functions small and well-documented.
* Write tests for new functionality.

## Reporting Issues

* Use GitHub Issues for bugs and feature requests.
* Include steps to reproduce, expected vs actual behavior, and your environment.

## License

By contributing, you agree that your contributions will be licensed under the
MIT License.
