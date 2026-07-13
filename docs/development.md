# Development Guide

## Setup

Install dependencies including dev dependencies:

```bash
poetry install --with dev
```

Install both Git hook stages:

```bash
poetry run pre-commit install
poetry run pre-commit install --hook-type pre-push
```

The pre-push hook runs heavier local checks like Pyright and pytest before pushing.

## Running the App

Enter the virtual environment:

```bash
poetry shell
```

Then run the application:

```bash
resume-roast
```

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
