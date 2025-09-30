# Zero Trust Architecture (ZTA) Simulator

A Python-based simulation testbed for evaluating Zero Trust Architecture (ZTA) controls in hybrid work environments. Generate synthetic events, simulate attacks, and analyze the effectiveness of ZTA policies.

## Architecture

```mermaid
graph LR
    RemoteUser[Remote User] --> ZTAGateway
    subgraph ZTAGateway[ZTA Gateway]
        Auth[Authentication]
        Posture[Device Posture]
        Seg[Micro-segmentation]
    end
    ZTAGateway --> Resource[Protected Resource]
    Attacker[Attacker] -.-> ZTAGateway
    ZTAGateway --> Logger[Central Logger]
    Logger --> Analysis[Analysis & Reporting]
```

## Quick Start

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Generate sample events:
```bash
python -m src.sim.run_sim --count 25 --out data/sample_logs.jsonl
```

4. Run tests:
```bash
pytest -v
```

## Project Structure

```
my-zta-project/
├── src/
│   ├── sim/          # Simulation engine
│   ├── controls/     # ZTA control implementations
│   ├── logging/      # Centralized logging
│   └── api/          # Optional FastAPI service
├── tests/            # Test suite
├── data/             # Generated data & logs
├── analysis/         # Analysis notebooks & scripts
└── configs/          # Experiment configurations
```

## Development

- Python 3.11+
- Type hints enforced
- Tests with pytest
- Black for formatting
- Flake8 for linting
- MyPy for type checking

## License

MIT

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
