SHELL      := /bin/bash

snake:
	PYTHONPATH=${PYTHONPATH}:$(pwd)/src python3 src/snake.py
.PHONY: snake

