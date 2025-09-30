# Contributing to ZTA Simulator

Thank you for your interest in contributing to the Zero Trust Architecture (ZTA) Simulator! This document provides guidelines and instructions for contributing.

## Code of Conduct

This project adheres to a Code of Conduct that all participants are expected to follow. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

## Development Setup

1. Create a virtual environment:
```bash
make setup
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
```

2. Install dependencies:
```bash
make install
```

3. Run tests to verify setup:
```bash
make test
```

## Development Workflow

1. Create a new branch for your feature/fix:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes, following our coding standards:
   - Use type hints
   - Add docstrings for public functions/classes
   - Follow PEP 8 style guide
   - Keep functions focused and modular

3. Run linting and tests:
```bash
make lint
make test
```

4. Format code:
```bash
make format
```

5. Commit your changes using conventional commits:
   - feat: New feature
   - fix: Bug fix
   - docs: Documentation changes
   - test: Test changes
   - chore: Maintenance tasks
   - refactor: Code refactoring
   - style: Code style changes

Example:
```bash
git commit -m "feat(auth): add MFA support"
```

6. Push your changes and create a pull request.

## Running Experiments

1. Generate sample events:
```bash
make run-sim
```

2. Run a full experiment:
```bash
make experiment
```

3. Run analysis and generate report:
```bash
make pipeline
```

## Project Structure

- `src/` - Core simulation code
  - `sim/` - Simulation engine
  - `controls/` - ZTA controls
  - `logging/` - Logging facilities
  - `api/` - Optional FastAPI service
- `tests/` - Test suite
- `analysis/` - Analysis tools and notebooks
- `configs/` - Experiment configurations
- `data/` - Generated data and logs
- `infra/` - Docker and deployment files

## Testing

- Write tests for new features
- Maintain test coverage
- Use pytest fixtures for common setup
- Mock external dependencies

## Documentation

- Update docstrings for new/modified code
- Keep README.md current
- Document configuration options
- Add examples for new features

## Release Process

1. Update version in setup.py
2. Update CHANGELOG.md
3. Create release branch
4. Run full test suite
5. Create GitHub release
6. Tag version

## Getting Help

- Open an issue for bugs/features
- Use discussions for questions
- Tag maintainers for urgent issues

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
