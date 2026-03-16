lint:
	@ruff check . --fix
	@ruff format .
.PHONY: lint

test:
	python -m coverage run -m pytest tests/ -v && \
	python -m coverage report
.PHONY: test