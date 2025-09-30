"""
Docker smoke tests.
"""

import json
import os
import subprocess
from pathlib import Path

import pytest

@pytest.mark.docker
def test_docker_build(tmp_path):
    """Test building Docker image."""
    # Build image
    result = subprocess.run(
        ["docker", "build", "-t", "zta-sim", "-f", "infra/Dockerfile", "."],
        capture_output=True,
        text=True,
        check=True
    )
    assert result.returncode == 0

@pytest.mark.docker
def test_docker_run(tmp_path, sample_config):
    """Test running experiment in Docker."""
    # Create output directory
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    # Copy config to output dir
    config_path = Path(sample_config)
    docker_config = output_dir / config_path.name
    docker_config.write_text(config_path.read_text())
    
    # Run container
    result = subprocess.run(
        [
            "docker", "run",
            "--rm",
            "-v", f"{output_dir}:/app/data",
            "zta-sim",
            "python", "-m", "src.sim.experiment",
            "--config", f"/app/data/{config_path.name}",
            "--run-id", "docker_test"
        ],
        capture_output=True,
        text=True,
        check=True
    )
    assert result.returncode == 0
    
    # Check outputs
    exp_dir = output_dir / "experiments" / "docker_test"
    assert exp_dir.exists()
    assert (exp_dir / "results.json").exists()
    
    # Check results
    results = json.loads((exp_dir / "results.json").read_text())
    assert "baseline" in results
    assert "zta" in results

@pytest.mark.docker
def test_docker_environment():
    """Test Docker environment variables."""
    result = subprocess.run(
        [
            "docker", "run",
            "--rm",
            "zta-sim",
            "python", "-c",
            "import os; print(os.environ.get('PYTHONPATH'))"
        ],
        capture_output=True,
        text=True,
        check=True
    )
    assert result.returncode == 0
    assert "/app" in result.stdout

@pytest.mark.skipif(
    os.environ.get("CI") != "true",
    reason="Only run in CI environment"
)
@pytest.mark.docker
def test_docker_ci_artifacts(tmp_path):
    """Test Docker artifacts in CI."""
    # Create output directory
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    # Run container with tiny experiment
    result = subprocess.run(
        [
            "docker", "run",
            "--rm",
            "-v", f"{output_dir}:/app/data",
            "-e", "RUN_COUNT=5",
            "zta-sim"
        ],
        capture_output=True,
        text=True,
        check=True
    )
    assert result.returncode == 0
    
    # Check artifacts
    artifacts = list(output_dir.glob("**/*"))
    assert len(artifacts) > 0
    
    # Check experiment outputs
    exp_dirs = list(output_dir.glob("experiments/*"))
    assert len(exp_dirs) > 0
    
    # Check results
    results_files = list(output_dir.glob("**/results.json"))
    assert len(results_files) > 0
