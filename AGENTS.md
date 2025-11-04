# Agent Guidelines for hackaton-open-overheid-poc

## Build/Lint/Test Commands
```bash
uv sync --group dev                    # Install dependencies and dev tools
uv run ruff check .                    # Check for linting errors
uv run ruff check --fix .              # Auto-fix safe linting issues
uv run pytest                          # Run all tests
uv run pytest test_file.py::test_name  # Run single test
uv run pytest -v                       # Run tests with verbose output
```

## Code Style Guidelines
- **Python**: 3.12+, line length 120 chars, Ruff (E, F, W, I, UP, T)
- **Naming**: snake_case vars/functions, PascalCase classes, UPPER_CASE constants
- **Imports**: stdlib → third-party → local; use `from __future__ import annotations`
- **Types**: Type hint all attributes/parameters/returns; use dataclasses for structured data
- **Error Handling**: Specific exceptions; broad `except Exception` with `# noqa: BLE001` for external calls
- **Logging**: `logger = logging.getLogger(__name__)` with appropriate levels
- **Docs**: Concise docstrings for classes/functions; prefer type hints over docstring types
- **File Rules**: Allow F401 in `__init__.py`; allow E501 in `metadata_extractor.py`