SHELL      := /bin/bash

setup-local:
	git submodule sync && git submodule update --init --recursive --remote
	poetry config --local virtualenvs.in-project true
	poetry install
	pre-commit install
.PHONY: setup-local

test:
	poetry run pytest -x -vv
.PHONY: test

run:
	poetry run python console.py -r ./nes-test-roms/instr_test-v5/official_only.nes
.PHONY: run
