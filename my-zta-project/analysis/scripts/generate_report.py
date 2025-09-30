"""
Zero Trust Architecture (ZTA) Report Generator

This module generates a Markdown report summarizing experiment results.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from src.sim.usability_metrics import UsabilityAnalyzer

class ReportGenerator:
    """Generates experiment summary reports."""
    
    def __init__(self, experiment_dir: Path):
        """
        Initialize with experiment directory.
        
        Args:
            experiment_dir: Path to experiment output directory
        """
        self.experiment_dir = Path(experiment_dir)
        
        # Load experiment config
        with open(self.experiment_dir / "config.json") as f:
            self.config = json.load(f)
        
        # Load results
        with open(self.experiment_dir / "results.json") as f:
            self.results = json.load(f)
    
    def _load_scenario_data(self, scenario: str) -> pd.DataFrame:
        """Load data for a specific scenario."""
        events_file = self.experiment_dir / scenario / "events.jsonl"
        if events_file.exists():
            return pd.read_json(events_file, lines=True, convert_dates=["timestamp"])
        return pd.DataFrame()
    
    def _format_metrics(self, metrics: Dict) -> str:
        """Format metrics as Markdown table rows."""
        rows = []
        for key, value in metrics.items():
            if isinstance(value, float):
                rows.append(f"| {key} | {value:.2f} |")
            else:
                rows.append(f"| {key} | {value} |")
        return "\n".join(rows)
    
    def generate_report(self, output_file: Optional[Path] = None) -> None:
        """
        Generate experiment report.
        
        Args:
            output_file: Optional output file path
        """
        if output_file is None:
            output_file = self.experiment_dir / "report.md"
        
        # Start building report
        sections = []
        
        # Header
        sections.extend([
            "# Zero Trust Architecture (ZTA) Experiment Report",
            "",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Experiment Configuration",
            "",
            f"- Experiment Name: {self.config['experiment_name']}",
            f"- Description: {self.config['description']}",
            f"- Seed: {self.config['seed']}",
            "",
            "## Scenarios",
            ""
        ])
        
        # Add scenario details
        for scenario in self.config["scenarios"]:
            sections.extend([
                f"### {scenario['name']}",
                "",
                f"Description: {scenario['description']}",
                "",
                "Controls:",
                "".join([f"- {k}: {'enabled' if v else 'disabled'}"
                        for k, v in scenario['controls'].items()]),
                "",
                "Attack Profile:",
                "".join([f"- {k}: {v}"
                        for k, v in scenario['attack_profile'].items()]),
                "",
                "Results:",
                "",
                "| Metric | Value |",
                "|--------|--------|",
                self._format_metrics(self.results[scenario["name"]]),
                ""
            ])
        
        # Add security analysis
        sections.extend([
            "## Security Analysis",
            "",
            "### Attack Prevention",
            ""
        ])
        
        # Compare attack success rates
        baseline_data = self._load_scenario_data("baseline")
        zta_data = self._load_scenario_data("zta_full")
        
        if not baseline_data.empty and not zta_data.empty:
            baseline_attacks = baseline_data[baseline_data["attack_type"].notna()]
            zta_attacks = zta_data[zta_data["attack_type"].notna()]
            
            if not baseline_attacks.empty and not zta_attacks.empty:
                baseline_rate = baseline_attacks["success"].mean()
                zta_rate = zta_attacks["success"].mean()
                
                sections.extend([
                    "Attack Success Rates:",
                    "",
                    f"- Baseline: {baseline_rate:.2%}",
                    f"- ZTA: {zta_rate:.2%}",
                    f"- Improvement: {(baseline_rate - zta_rate):.2%}",
                    ""
                ])
        
        # Add usability analysis
        sections.extend([
            "## Usability Analysis",
            "",
            "### Task Completion",
            ""
        ])
        
        # Calculate usability metrics
        analyzer = UsabilityAnalyzer()
        for scenario in self.config["scenarios"]:
            data = self._load_scenario_data(scenario["name"])
            if not data.empty:
                metrics = analyzer.calculate_metrics(data)
                
                sections.extend([
                    f"#### {scenario['name']}",
                    "",
                    f"- SUS Score: {metrics.sus_score:.1f}",
                    f"- Task Completion Rate: {metrics.task_completion_rate:.2%}",
                    f"- Average Task Duration: {metrics.avg_task_duration:.1f}s",
                    f"- Friction Events per Task: {metrics.friction_events_per_task:.2f}",
                    f"- User Satisfaction: {metrics.satisfaction_score:.1f}/5.0",
                    ""
                ])
        
        # Add recommendations
        sections.extend([
            "## Recommendations",
            "",
            "Based on the experiment results, we recommend:",
            "",
            "1. **Security Improvements**",
            "   - Implement all ZTA controls for critical resources",
            "   - Use MFA for sensitive operations",
            "   - Regular device posture checks",
            "",
            "2. **Usability Optimizations**",
            "   - Cache device posture results to reduce checks",
            "   - Implement session persistence for common operations",
            "   - Provide clear feedback on access decisions",
            "",
            "3. **Monitoring & Response**",
            "   - Set up alerts for repeated access failures",
            "   - Monitor device compliance trends",
            "   - Regular review of access patterns",
            ""
        ])
        
        # Write report
        with open(output_file, "w") as f:
            f.write("\n".join(sections))

def main():
    """Main entry point for report generation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate experiment report")
    parser.add_argument("--experiment", type=str, required=True,
                       help="Path to experiment directory")
    parser.add_argument("--output", type=str,
                       help="Output report file path")
    
    args = parser.parse_args()
    
    generator = ReportGenerator(Path(args.experiment))
    generator.generate_report(
        Path(args.output) if args.output else None
    )

if __name__ == "__main__":
    main()
