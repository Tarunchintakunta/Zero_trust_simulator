# Project Verification Guide

This document describes how to verify that the ZTA simulator project is working correctly.

## Quick Verification

Run the verification script:

```bash
./scripts/verify_project.py
```

This will run all verification checks and report any issues.

To use a temporary directory for outputs:

```bash
./scripts/verify_project.py --tmp
```

## Manual Verification Steps

### 1. Environment Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt
pip install -e .
```

### 2. Run Tests

```bash
# Run tests with coverage
pytest -v --cov=src --cov-report=term-missing

# Check coverage meets 80% threshold
coverage report --fail-under=80
```

### 3. Run Simulations

```bash
# Generate baseline events
python -m src.sim.run_sim --count 10 --out data/verify_baseline.jsonl --mode baseline --seed 1

# Run ZTA experiment
python -m src.sim.experiment --config configs/sample_experiment.json --mode zta --run-id verify_zta --seed 1

# Run analysis
python -m analysis.scripts.analyze_results --input data/experiments/verify_zta --out data/experiments/verify_zta/report.csv

# Run usability simulation
python -m src.sim.usability --count 10 --out data/usability_test.csv --seed 2
```

### 4. Docker Verification

```bash
# Build image
docker build -t zta-sim -f infra/Dockerfile .

# Run experiment
docker run --rm -v "$(pwd)/data:/app/data" zta-sim
```

## Acceptance Criteria

1. Tests:
   - All tests pass
   - Coverage ≥ 80%
   - No linting errors

2. Simulation:
   - Baseline events generated
   - ZTA experiment runs
   - Analysis produces report
   - Usability metrics collected

3. Docker:
   - Image builds successfully
   - Container runs experiment
   - Results written to mounted volume

## Troubleshooting

### Common Issues

1. Import errors:
   - Ensure you're in the virtual environment
   - Verify package is installed in editable mode

2. File not found:
   - Check working directory
   - Verify config paths are correct

3. Docker issues:
   - Check Docker daemon is running
   - Verify volume mount paths

### Getting Help

1. Check error messages in:
   - Test output
   - Coverage report
   - Docker build logs

2. Review logs in:
   - data/experiments/*/events.jsonl
   - data/experiments/*/results.json

3. For Docker:
   - Check container logs
   - Verify file permissions

## CI/CD Integration

The project includes GitHub Actions workflows that:

1. Run tests and coverage
2. Build Docker image
3. Run smoke test
4. Upload artifacts

Check `.github/workflows/ci.yml` for details.
