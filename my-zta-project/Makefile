.PHONY: venv install clean test lint run-sim experiment docker-build docker-run

# Python settings
PYTHON = python3.11
VENV = venv
BIN = $(VENV)/bin

# Project settings
CONFIG = configs/sample_experiment.json
OUTPUT = data/sample_logs.jsonl

# Create virtual environment
venv:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -r requirements.txt
	$(BIN)/pip install -e .

# Install dependencies
install:
	$(BIN)/pip install -r requirements.txt
	$(BIN)/pip install -e .

# Clean up generated files
clean:
	rm -rf __pycache__
	rm -rf *.pyc
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf build
	rm -rf dist
	rm -rf *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} +

# Run tests
test:
	$(BIN)/pytest -v --cov=src

# Run linting
lint:
	$(BIN)/flake8 src tests
	$(BIN)/mypy src tests
	$(BIN)/black --check src tests

# Format code
format:
	$(BIN)/black src tests

# Run simulation
run-sim:
	$(BIN)/python -m src.sim.run_sim --count 25 --out $(OUTPUT)

# Run experiment
experiment:
	$(BIN)/python -m src.sim.experiment --config $(CONFIG)

# Run analysis
analyze:
	$(BIN)/python -m analysis.scripts.analyze_results --experiment data/experiments/$(shell ls -t data/experiments | head -n1)

# Generate report
report:
	$(BIN)/python -m analysis.scripts.generate_report --experiment data/experiments/$(shell ls -t data/experiments | head -n1)

# Run full experiment pipeline
pipeline: experiment analyze report

# Docker commands
docker-build:
	docker-compose -f infra/docker-compose.yml build

docker-run:
	docker-compose -f infra/docker-compose.yml up

# Development setup
setup: venv install
	@echo "Development environment ready!"
	@echo "Activate with: source venv/bin/activate"

# Help target
help:
	@echo "Available targets:"
	@echo "  venv        - Create virtual environment and install dependencies"
	@echo "  install     - Install dependencies in existing venv"
	@echo "  clean       - Clean up generated files"
	@echo "  test        - Run tests with coverage"
	@echo "  lint        - Run linting checks"
	@echo "  format      - Format code with black"
	@echo "  run-sim     - Run simulation"
	@echo "  experiment  - Run experiment"
	@echo "  analyze     - Run analysis"
	@echo "  report      - Generate report"
	@echo "  pipeline    - Run full experiment pipeline"
	@echo "  docker-build- Build Docker image"
	@echo "  docker-run  - Run in Docker"
	@echo "  setup       - Set up development environment"
