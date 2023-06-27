SHELL      := /bin/bash

setup-local:
	poetry config --local virtualenvs.in-project true
	poetry install
	pre-commit install
.PHONY: setup-local

test:
	poetry run pytest
.PHONY: test

run:
	poetry run python console.py -r roms/ines-1x16PGR-1x8kCHR.rm
.PHONY: run
