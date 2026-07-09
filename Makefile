.PHONY: test report fix format format-check lint typecheck check

test:
	poetry run coverage run -m pytest

report:
	poetry run coverage report -m

fix:
	poetry run ruff check --fix .

format:
	poetry run ruff format .

format-check:
	poetry run ruff format --check .

lint:
	poetry run ruff check .

typecheck:
	poetry run pyright

check: format-check lint typecheck test
