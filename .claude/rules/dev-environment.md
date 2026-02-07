# Development Environment

Project development environment and toolchain.

## Windows Requirements

On Windows, some Unix utilities used by Claude Code's Bash tool require additional setup:

- **touch, chmod, wc, uniq, pkill, etc.**: Install via [MSYS2](https://www.msys2.org/) or [Git Bash](https://git-scm.com/downloads) (includes busybox)
- **Alternative**: Use WSL2 for full POSIX compatibility

The hook scripts and core functionality work with native Windows Python.

## Package Management: uv

**Do not use pip directly. All commands must go through uv.**

```powershell
# Add packages
uv add <package>
uv add --dev <package>    # Dev dependency

# Sync dependencies
uv sync

# Run scripts
uv run <command>
uv run python script.py
uv run pytest
```

### pyproject.toml

Manage dependencies in `pyproject.toml`:

```toml
[project]
dependencies = [
    "httpx>=0.27",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "ruff>=0.8",
]
```

## Linting & Formatting: ruff

```powershell
# Check
uv run ruff check .

# Auto-fix
uv run ruff check --fix .

# Format
uv run ruff format .
```

### ruff Configuration (pyproject.toml)

```toml
[tool.ruff]
target-version = "py312"
line-length = 88

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # pyflakes
    "I",      # isort
    "B",      # flake8-bugbear
    "UP",     # pyupgrade
]
ignore = ["E501"]  # line too long (formatter handles)

[tool.ruff.format]
quote-style = "double"
```

## Type Checking: ty

```powershell
# Run type check
uv run ty check src\\
```

### ty Features

- Fast Rust-based type checker (by Astral)
- Same ecosystem as ruff / uv
- mypy-compatible type annotations

## Notebooks: marimo

Interactive Python notebook environment.

```powershell
# Create/edit notebook
uv run marimo edit notebook.py

# Run notebook (CLI)
uv run marimo run notebook.py

# Deploy as app
uv run marimo run notebook.py --host 0.0.0.0 --port 8080
```

### marimo Features

- **Pure Python files** (.py): Git-friendly
- **Reactive**: Auto-tracks cell dependencies
- **Reproducible**: No execution order dependency

### marimo Best Practices

```python
# Bad: Mutating global state
data = []
def add_item(item):
    data.append(item)  # Side effect

# Good: Pure function
def add_item(data: list, item) -> list:
    return [*data, item]
```

## Task Runner

Manage multiple tool executions in `pyproject.toml` scripts or poe:

```toml
[tool.poe.tasks]
lint = "ruff check . && ruff format --check ."
format = "ruff check --fix . && ruff format ."
typecheck = "ty check src/"
test = "pytest -v"
all = ["lint", "typecheck", "test"]
```

## Common Commands

```powershell
# Initialize
uv init
uv venv
.\\.venv\\Scripts\\Activate.ps1

# Install dev dependencies
uv sync --all-extras

# Quality check (all)
uv run ruff check . && uv run ruff format --check . && uv run ty check src\\ && uv run pytest

# Or via poe
poe all
```

## Pre-commit Checklist

- [ ] `uv run ruff check .` passes
- [ ] `uv run ruff format --check .` passes
- [ ] `uv run ty check src/` passes
- [ ] `uv run pytest` passes
