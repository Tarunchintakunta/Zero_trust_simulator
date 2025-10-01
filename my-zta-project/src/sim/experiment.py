"""
Zero Trust Architecture (ZTA) Experiment Runner

This module runs experiments comparing baseline vs ZTA configurations.
"""

import argparse
import json
import logging
import pandas as pd
from datetime import datetime
from typing import Dict

from src.logging.central_logger import get_logger
from src.sim.attacks import AttackSimulator, AttackType
from src.sim.run_sim import generate_events
from src.utils.config import (
    load_config,
    merge_cli_args,
    set_seed,
    validate_config,
    get_output_dir,
)


class ExperimentRunner:
    """Runs ZTA experiments and collects results."""

    def __init__(self, config: Dict):
        """
        Initialize with experiment configuration.

        Args:
            config: Experiment configuration dict
        """
        self.config = config

        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Create output directory
        base_dir = (
            self.config.get("output_dir") or self.config["output"]["base_dir"]
        )
        run_id = self.config.get(
            "run_id", datetime.now().strftime("%Y%m%d_%H%M%S")
        )
        self.output_dir = get_output_dir(base_dir, run_id)

        # Save config copy
        with open(self.output_dir / "config.json", "w") as f:
            json.dump(self.config, f, indent=2)

    def _run_scenario(self, scenario: Dict) -> Dict:
        """Run a single scenario and collect results."""
        scenario_dir = self.output_dir / scenario["name"]
        scenario_dir.mkdir(exist_ok=True)

        # Set up logging for this scenario
        log_path = scenario_dir / "events.jsonl"
        scenario_logger = get_logger(log_path)

        # Generate normal traffic
        self.logger.info(
            f"Gen {scenario['sim_count']} events for {scenario['name']}"
        )

        # Apply mode override if provided
        use_controls = (
            self.config.get("mode") == "zta"
            if "mode" in self.config
            else scenario["controls"]["auth"]
        )

        normal_events = generate_events(
            count=scenario["sim_count"],
            seed=self.config["seed"],
            use_controls=use_controls,
        )

        # Log normal events
        for event in normal_events:
            scenario_logger.log_event(event)

        # Run attack simulation if enabled
        if scenario.get("attack_profile", {}).get("enabled", False):
            attack_profile = scenario["attack_profile"]
            attack_sim = AttackSimulator(seed=self.config["seed"])

            if attack_profile["type"] == AttackType.CREDENTIAL_STUFFING:
                self.logger.info(f"Cred stuffing in {scenario['name']}")
                attack_events = attack_sim.simulate_credential_stuffing(
                    target_users=attack_profile["target_users"],
                    attempts=attack_profile["attempts"],
                )

            elif attack_profile["type"] == AttackType.LATERAL_MOVEMENT:
                self.logger.info(f"Lateral movement in {scenario['name']}")
                attack_events = attack_sim.simulate_lateral_movement(
                    compromised_user=attack_profile["compromised_user"],
                    target_resources=attack_profile["target_resources"],
                    attempts=attack_profile["attempts"],
                )

            elif attack_profile["type"] == AttackType.RANSOMWARE:
                self.logger.info(f"Ransomware attack in {scenario['name']}")
                attack_events = attack_sim.simulate_ransomware(
                    compromised_user=attack_profile["compromised_user"],
                    target_resources=attack_profile["target_resources"],
                    encryption_attempts=attack_profile["attempts"],
                )

            # Log attack events
            for event in attack_events:
                scenario_logger.log_event(event)

        # Calculate basic metrics
        total_events = len(normal_events)
        successful_events = sum(1 for e in normal_events if e["success"])
        failed_events = total_events - successful_events

        metrics = {
            "total_events": total_events,
            "successful_events": successful_events,
            "failed_events": failed_events,
            "success_rate": (
                successful_events / total_events if total_events > 0 else 0
            ),
        }

        # Save metrics
        with open(scenario_dir / "metrics.json", "w") as f:
            json.dump(metrics, f, indent=2)

        return metrics

    def run(self) -> Dict[str, Dict]:
        """
        Run all scenarios in the experiment.

        Returns:
            Dict mapping scenario names to their metrics
        """
        results = {}

        for scenario in self.config["scenarios"]:
            self.logger.info(f"Running scenario: {scenario['name']}")
            metrics = self._run_scenario(scenario)
            results[scenario["name"]] = metrics

        # Save overall results as JSON
        with open(self.output_dir / "results.json", "w") as f:
            json.dump(results, f, indent=2)

        # Save results as CSV for analysis
        df = pd.DataFrame.from_dict(results, orient="index")
        df.to_csv(self.output_dir / "report.csv")

        return results


def main():
    """Main entry point for running experiments."""
    parser = argparse.ArgumentParser(description="Run ZTA experiments")
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to experiment config JSON",
    )
    parser.add_argument(
        "--mode",
        choices=["baseline", "zta"],
        help="Override mode for all scenarios",
    )
    parser.add_argument(
        "--run-id", type=str, help="Unique identifier for this run"
    )
    parser.add_argument(
        "--seed", type=int, help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--output-dir", type=str, help="Base directory for outputs"
    )

    args = parser.parse_args()

    # Load config
    config = load_config(args.config)

    # Merge CLI args
    config = merge_cli_args(config, args)

    # Validate config
    required = ["scenarios", "seed", "output"]
    validate_config(config, required)

    # Set seed
    set_seed(config["seed"])

    # Run experiment
    runner = ExperimentRunner(config)
    results = runner.run()

    # Print summary
    print("\nExperiment Results:")
    for scenario, metrics in results.items():
        print(f"\n{scenario}:")
        print(f"  Total Events: {metrics['total_events']}")
        print(f"  Success Rate: {metrics['success_rate']:.2%}")


if __name__ == "__main__":
    main()
