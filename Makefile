# Set up environment variables
PYTHON = .venv/bin/python3
PYTHONPATH = PYTHONPATH=./

help: ## Show this help message
	@echo "Whynes"
	@echo "===================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

clean: ## Clean up build artifacts
	rm -rf build dist .egg-info .pytest_cache .coverage .mypy_cache .tox

snake: setup ## Run the game with default settings
	$(PYTHONPATH) $(PYTHON) src/snake.py

create_venv: ## Create a virtual environment
	@if [ ! -d "./.venv" ]; then \
		python -m venv .venv; \
	fi

setup: create_venv ## Create and activate the virtual environment
	@if ! $(PYTHON) -m pip show pygame > /dev/null 2>&1; then \
		$(PYTHON) -m pip install --upgrade pip; \
		$(PYTHON) -m pip install -e .[dev]; \
	fi

test: setup ## Run tests
	$(PYTHONPATH) $(PYTHON) -m pytest -v

