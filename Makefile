SHELL      := /bin/bash

setup-local:
	poetry config --local virtualenvs.in-project true
	poetry install
	pre-commit install
.PHONY: setup-local

run:
	.venv/bin/python3 console.py -r roms/ines-1x16PGR-1x8kCHR.rom
.PHONY: run
