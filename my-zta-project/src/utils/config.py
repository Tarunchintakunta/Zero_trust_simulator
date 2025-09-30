"""
Configuration utilities for ZTA simulator.
"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Optional, Union

import numpy as np
import random


def set_seed(seed: Optional[int] = None) -> None:
    """Set random seeds for reproducibility."""
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)


def load_config(config_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load configuration from JSON file.

    Args:
        config_path: Path to config JSON file

    Returns:
        Dict containing config values

    Raises:
        FileNotFoundError: If config file doesn't exist
        json.JSONDecodeError: If config is invalid JSON
    """
    with open(config_path) as f:
        return json.load(f)


def merge_cli_args(config: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Any]:
    """
    Merge CLI arguments into config, with CLI taking precedence.

    Args:
        config: Base configuration dict
        args: Parsed CLI arguments

    Returns:
        Updated config dict
    """
    merged = config.copy()

    # Convert args to dict, excluding None values
    cli_dict = {k: v for k, v in vars(args).items() if v is not None and k != "config"}

    # Update config with CLI values
    merged.update(cli_dict)

    return merged


def get_output_dir(base_dir: Union[str, Path], run_id: str) -> Path:
    """
    Get output directory path, creating if needed.

    Args:
        base_dir: Base directory for outputs
        run_id: Unique run identifier

    Returns:
        Path to output directory
    """
    out_dir = Path(base_dir) / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def validate_config(config: Dict[str, Any], required_keys: list[str]) -> None:
    """
    Validate config has required keys.

    Args:
        config: Configuration dict to validate
        required_keys: List of required key names

    Raises:
        ValueError: If any required keys are missing
    """
    missing = [key for key in required_keys if key not in config]
    if missing:
        raise ValueError(f"Missing required config keys: {missing}")
