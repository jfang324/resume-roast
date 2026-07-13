.PHONY: test report fix format format-check lint typecheck check clean

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

clean:
	powershell -NoProfile -Command "Get-ChildItem -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force"
	powershell -NoProfile -Command "Get-ChildItem -Recurse -Include *.pyc,*.pyo | Remove-Item -Force"
	powershell -NoProfile -Command "Remove-Item -Recurse -Force .pytest_cache,.coverage -ErrorAction SilentlyContinue"
