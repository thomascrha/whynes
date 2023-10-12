SHELL      := /bin/bash

test:
	pytest -x -vv
.PHONY: test

run:
	python3 console.py -r ./nes-test-roms/instr_test-v5/official_only.nes
.PHONY: run
