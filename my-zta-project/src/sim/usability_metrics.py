"""
Zero Trust Architecture (ZTA) Usability Metrics

This module calculates various usability metrics including SUS scores.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from src.sim.usability import TaskResult


@dataclass
class UsabilityMetrics:
    """Collection of usability metrics."""

    sus_score: float
    task_completion_rate: float
    avg_task_duration: float
    friction_events_per_task: float
    satisfaction_score: float
    detailed_metrics: Dict[str, float]


class SUSConfig:
    """Configuration for SUS score calculation."""

    def __init__(self):
        """Initialize with default values."""
        self.scale_multiplier = 2.5  # Convert 0-40 to 0-100
        self.max_friction_penalty = 4  # Maximum points deducted for friction
        self.early_results_fraction = (
            1 / 3
        )  # Fraction of results to consider "early"
        self.questions = [
            "I think that I would like to use this system frequently",
            "I found the system unnecessarily complex",
            "I thought the system was easy to use",
            "I think that I would need support to use this system",
            "I found the various functions well integrated",
            "I thought there was too much inconsistency",
            "Most people would learn to use this system quickly",
            "I found the system very cumbersome to use",
            "I felt very confident using the system",
            "I needed to learn a lot before I could use this system",
        ]


class SUSCalculator:
    """Calculates System Usability Scale (SUS) scores."""

    def __init__(self, config: Optional[SUSConfig] = None):
        """Initialize with configuration."""
        self.config = config or SUSConfig()

    def _simulate_responses(self, results: List[TaskResult]) -> List[int]:
        """
        Simulate SUS question responses based on task results.

        Args:
            results: List of task results

        Returns:
            List of simulated responses (1-5 scale)
        """
        if not results:
            return [3] * len(self.questions)  # Neutral responses

        # Calculate metrics that influence responses
        success_rate = sum(1 for r in results if r.success) / len(results)
        avg_friction = sum(len(r.friction_events) for r in results) / len(
            results
        )
        avg_satisfaction = sum(r.satisfaction_score for r in results) / len(
            results
        )

        # Simulate responses based on metrics
        responses = []

        # Q1: Frequency of use (higher satisfaction = more likely to use)
        responses.append(round(avg_satisfaction))

        # Q2: Complexity (more friction = more complex)
        responses.append(
            round(1 + min(self.config.max_friction_penalty, avg_friction))
        )

        # Q3: Ease of use (higher success rate = easier)
        responses.append(round(success_rate * 5))

        # Q4: Need for support (more friction = more support needed)
        responses.append(
            round(1 + min(self.config.max_friction_penalty, avg_friction))
        )

        # Q5: Integration (based on satisfaction)
        responses.append(round(avg_satisfaction))

        # Q6: Inconsistency (based on friction variance)
        friction_variance = np.std([len(r.friction_events) for r in results])
        responses.append(
            round(1 + min(self.config.max_friction_penalty, friction_variance))
        )

        # Q7: Learnability (based on success rate trend)
        responses.append(round(success_rate * 5))

        # Q8: Cumbersome (based on friction)
        responses.append(
            round(1 + min(self.config.max_friction_penalty, avg_friction))
        )

        # Q9: Confidence (based on success rate)
        responses.append(round(success_rate * 5))

        # Q10: Learning curve (based on early success rate)
        early_count = max(
            1, int(len(results) * self.config.early_results_fraction)
        )
        early_results = results[:early_count]
        early_success = sum(1 for r in early_results if r.success) / len(
            early_results
        )
        responses.append(
            round(
                1
                + min(
                    self.config.max_friction_penalty, (1 - early_success) * 4
                )
            )
        )

        # Ensure all responses are in range 1-5
        return [max(1, min(5, r)) for r in responses]

    def calculate_sus(self, results: List[TaskResult]) -> float:
        """
        Calculate SUS score from task results.

        Args:
            results: List of task results

        Returns:
            SUS score (0-100)
        """
        if not results:
            return 0.0

        responses = self._simulate_responses(results)

        # Calculate SUS score
        score = 0
        for i, response in enumerate(responses):
            # Odd questions are positive (response - 1)
            # Even questions are negative (5 - response)
            if i % 2 == 0:
                score += response - 1
            else:
                score += 5 - response

        # Convert to 0-100 scale
        # Each question contributes 0-4 points (max 40 total)
        # Multiply by scale_multiplier to get 0-100 scale
        return score * self.config.scale_multiplier


class UsabilityAnalyzer:
    """Analyzes usability metrics from task results."""

    def __init__(self):
        """Initialize analyzers."""
        self.sus_calculator = SUSCalculator()

    def calculate_metrics(
        self, results: List[TaskResult], scenario: Optional[str] = None
    ) -> UsabilityMetrics:
        """
        Calculate all usability metrics.

        Args:
            results: List of task results
            scenario: Optional scenario name for context

        Returns:
            UsabilityMetrics object
        """
        if not results:
            return UsabilityMetrics(
                sus_score=0.0,
                task_completion_rate=0.0,
                avg_task_duration=0.0,
                friction_events_per_task=0.0,
                satisfaction_score=0.0,
                detailed_metrics={},
            )

        # Basic metrics
        completion_rate = sum(1 for r in results if r.success) / len(results)
        avg_duration = sum(r.duration.total_seconds() for r in results) / len(
            results
        )
        avg_friction = sum(len(r.friction_events) for r in results) / len(
            results
        )
        avg_satisfaction = sum(r.satisfaction_score for r in results) / len(
            results
        )

        # Calculate SUS score
        sus_score = self.sus_calculator.calculate_sus(results)

        # Detailed metrics by task type
        df = pd.DataFrame(
            [
                {
                    "type": r.task.type,
                    "duration": r.duration.total_seconds(),
                    "friction_count": len(r.friction_events),
                    "satisfaction": r.satisfaction_score,
                    "success": r.success,
                }
                for r in results
            ]
        )

        detailed = {}
        if not df.empty:
            for task_type in df["type"].unique():
                task_df = df[df["type"] == task_type]
                detailed.update(
                    {
                        f"{task_type}_completion_rate": task_df[
                            "success"
                        ].mean(),
                        f"{task_type}_avg_duration": task_df[
                            "duration"
                        ].mean(),
                        f"{task_type}_avg_friction": task_df[
                            "friction_count"
                        ].mean(),
                        f"{task_type}_satisfaction": task_df[
                            "satisfaction"
                        ].mean(),
                    }
                )

        return UsabilityMetrics(
            sus_score=sus_score,
            task_completion_rate=completion_rate,
            avg_task_duration=avg_duration,
            friction_events_per_task=avg_friction,
            satisfaction_score=avg_satisfaction,
            detailed_metrics=detailed,
        )
