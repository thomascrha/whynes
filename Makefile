SHELL      := /bin/bash

test:
	pytest -v src/cpu.py
.PHONY: test
