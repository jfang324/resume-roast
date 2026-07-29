# Development Guide

## Setup

Install dependencies, including the dev group:

```bash
poetry install
```

Install both Git hook stages:

```bash
poetry run pre-commit install
poetry run pre-commit install --hook-type pre-push
```

The pre-push hook runs heavier local checks like Pyright and pytest before pushing.

## Running the App

Run the application through Poetry:

```bash
poetry run resume-roast
```

To call `resume-roast` directly instead, activate the virtual environment first.
`poetry env activate` prints the activation command for your shell — run what it
prints:

```bash
poetry env activate
```

Poetry 2.x moved `poetry shell` out of core; install `poetry-plugin-shell` if you
prefer that command.

## Testing

Run all tests and generate coverage report:

```bash
make test
make report
```

Run a targeted test file or test case:

```bash
poetry run coverage run -m pytest tests/cli/refine/test_handlers.py -v
poetry run coverage run -m pytest tests/cli/refine/test_handlers.py::test_replace_updates_current_bullet_and_triggers_re_rating -v
```

## Code Quality

Run linting, type checking, formatting:

```bash
make check
```
