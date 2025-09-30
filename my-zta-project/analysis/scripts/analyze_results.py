"""
Zero Trust Architecture (ZTA) Results Analysis

This module analyzes experiment results and detects anomalies.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

class ResultAnalyzer:
    """Analyzes experiment results and generates metrics."""
    
    def __init__(self, experiment_dir: Path):
        """
        Initialize with experiment directory.
        
        Args:
            experiment_dir: Path to experiment output directory
        """
        self.experiment_dir = Path(experiment_dir)
        self.results: Dict[str, pd.DataFrame] = {}
        
        # Load results for each scenario
        for scenario_dir in self.experiment_dir.glob("*"):
            if scenario_dir.is_dir():
                events_file = scenario_dir / "events.jsonl"
                if events_file.exists():
                    self.results[scenario_dir.name] = pd.read_json(
                        events_file,
                        lines=True,
                        convert_dates=["timestamp"]
                    )
    
    def calculate_detection_latency(self) -> Dict[str, timedelta]:
        """
        Calculate time between first attack event and first detection.
        
        Returns:
            Dict mapping scenario names to detection latencies
        """
        latencies = {}
        
        for scenario, df in self.results.items():
            # Find first attack event
            attack_events = df[df["attack_type"].notna()]
            if len(attack_events) == 0:
                continue
            
            first_attack = attack_events["timestamp"].min()
            
            # Find first detection (failed auth/access after attack start)
            detections = df[
                (df["timestamp"] > first_attack) &
                (~df["success"]) &
                (df["decision"] == "deny")
            ]
            
            if len(detections) > 0:
                first_detection = detections["timestamp"].min()
                latencies[scenario] = first_detection - first_attack
        
        return latencies
    
    def calculate_encryption_rate(self) -> Dict[str, float]:
        """
        Calculate percentage of files encrypted in ransomware scenarios.
        
        Returns:
            Dict mapping scenario names to encryption rates
        """
        rates = {}
        
        for scenario, df in self.results.items():
            # Find ransomware events
            if "filename" not in df.columns:
                continue
                
            ransomware = df[
                (df["attack_type"] == "ransomware") &
                (df["event"] == "file_write") &
                (df["filename"].str.contains("encrypted_", na=False))
            ]
            
            if len(ransomware) > 0:
                successful = ransomware[ransomware["success"]].shape[0]
                total = ransomware.shape[0]
                rates[scenario] = successful / total if total > 0 else 0.0
        
        return rates
    
    def calculate_lateral_movement(self) -> Dict[str, Dict[str, int]]:
        """
        Calculate lateral movement statistics.
        
        Returns:
            Dict mapping scenario names to movement stats
        """
        stats = {}
        
        for scenario, df in self.results.items():
            lateral = df[df["attack_type"] == "lateral_movement"]
            if len(lateral) > 0:
                stats[scenario] = {
                    "attempts": lateral.shape[0],
                    "successful": lateral[lateral["success"]].shape[0],
                    "blocked": lateral[~lateral["success"]].shape[0]
                }
        
        return stats
    
    def calculate_auth_rates(self) -> Dict[str, Dict[str, float]]:
        """
        Calculate authentication success/failure rates.
        
        Returns:
            Dict mapping scenario names to auth rates
        """
        rates = {}
        
        for scenario, df in self.results.items():
            auth_events = df[df["event"] == "login"]
            if len(auth_events) > 0:
                total = auth_events.shape[0]
                success = auth_events[auth_events["success"]].shape[0]
                rates[scenario] = {
                    "success_rate": success / total if total > 0 else 0.0,
                    "failure_rate": (total - success) / total if total > 0 else 0.0
                }
        
        return rates
    
    def plot_metrics(self, output_dir: Optional[Path] = None) -> None:
        """
        Generate plots for key metrics.
        
        Args:
            output_dir: Optional output directory for plots
        """
        if output_dir is None:
            output_dir = self.experiment_dir / "figures"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Plot detection latencies
        latencies = self.calculate_detection_latency()
        if latencies:
            plt.figure(figsize=(10, 6))
            scenarios = list(latencies.keys())
            times = [l.total_seconds() for l in latencies.values()]
            plt.bar(scenarios, times)
            plt.title("Attack Detection Latency")
            plt.ylabel("Seconds")
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(output_dir / "detection_latency.png")
            plt.close()
        
        # Plot encryption rates
        rates = self.calculate_encryption_rate()
        if rates:
            plt.figure(figsize=(10, 6))
            scenarios = list(rates.keys())
            values = list(rates.values())
            plt.bar(scenarios, values)
            plt.title("Ransomware Encryption Success Rate")
            plt.ylabel("Rate")
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(output_dir / "encryption_rate.png")
            plt.close()
        
        # Plot lateral movement
        movement = self.calculate_lateral_movement()
        if movement:
            plt.figure(figsize=(10, 6))
            scenarios = list(movement.keys())
            blocked = [m["blocked"] for m in movement.values()]
            successful = [m["successful"] for m in movement.values()]
            
            x = np.arange(len(scenarios))
            width = 0.35
            
            plt.bar(x - width/2, blocked, width, label="Blocked")
            plt.bar(x + width/2, successful, width, label="Successful")
            plt.title("Lateral Movement Attempts")
            plt.xlabel("Scenario")
            plt.ylabel("Count")
            plt.xticks(x, scenarios, rotation=45)
            plt.legend()
            plt.tight_layout()
            plt.savefig(output_dir / "lateral_movement.png")
            plt.close()
        
        # Plot auth rates
        rates = self.calculate_auth_rates()
        if rates:
            plt.figure(figsize=(10, 6))
            scenarios = list(rates.keys())
            success_rates = [r["success_rate"] for r in rates.values()]
            failure_rates = [r["failure_rate"] for r in rates.values()]
            
            x = np.arange(len(scenarios))
            width = 0.35
            
            plt.bar(x - width/2, success_rates, width, label="Success")
            plt.bar(x + width/2, failure_rates, width, label="Failure")
            plt.title("Authentication Rates")
            plt.xlabel("Scenario")
            plt.ylabel("Rate")
            plt.xticks(x, scenarios, rotation=45)
            plt.legend()
            plt.tight_layout()
            plt.savefig(output_dir / "auth_rates.png")
            plt.close()
    
    def save_summary(self, output_file: Optional[Path] = None) -> None:
        """
        Save analysis summary as CSV.
        
        Args:
            output_file: Optional output file path
        """
        if output_file is None:
            output_file = self.experiment_dir / "summary.csv"
        
        # Collect all metrics
        summary = []
        
        latencies = self.calculate_detection_latency()
        rates = self.calculate_encryption_rate()
        movement = self.calculate_lateral_movement()
        auth = self.calculate_auth_rates()
        
        for scenario in self.results.keys():
            row = {
                "scenario": scenario,
                "detection_latency": latencies.get(scenario, pd.NA),
                "encryption_rate": rates.get(scenario, pd.NA),
                "lateral_movement_blocked": movement.get(scenario, {}).get("blocked", 0),
                "lateral_movement_success": movement.get(scenario, {}).get("successful", 0),
                "auth_success_rate": auth.get(scenario, {}).get("success_rate", pd.NA),
                "auth_failure_rate": auth.get(scenario, {}).get("failure_rate", pd.NA)
            }
            summary.append(row)
        
        # Save to CSV
        pd.DataFrame(summary).to_csv(output_file, index=False)

def main():
    """Main entry point for analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze ZTA experiment results")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--experiment", type=str,
                      help="Path to experiment directory")
    group.add_argument("--input", type=str,
                      help="Path to experiment directory (alias for --experiment)")
    parser.add_argument("--output", type=str,
                       help="Output directory for analysis artifacts")
    
    args = parser.parse_args()
    
    experiment_dir = Path(args.experiment or args.input)
    output_dir = Path(args.output) if args.output else experiment_dir / "analysis"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    analyzer = ResultAnalyzer(experiment_dir)
    analyzer.plot_metrics(output_dir / "figures")
    analyzer.save_summary(output_dir / "summary.csv")

if __name__ == "__main__":
    main()
