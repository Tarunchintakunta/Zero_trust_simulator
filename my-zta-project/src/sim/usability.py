"""
Zero Trust Architecture (ZTA) Usability Simulation

This module simulates user interactions and measures usability metrics.
"""

import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional

class TaskType(str, Enum):
    """Types of user tasks."""
    LOGIN = "login"
    ACCESS_FILE = "access_file"
    EDIT_FILE = "edit_file"
    RUN_REPORT = "run_report"
    ADMIN_TASK = "admin_task"

@dataclass
class Task:
    """Represents a user task."""
    type: TaskType
    user: str
    device: str
    resource: Optional[str] = None
    requires_mfa: bool = False
    expected_duration: timedelta = timedelta(minutes=5)

@dataclass
class TaskResult:
    """Result of a task attempt."""
    task: Task
    success: bool
    duration: timedelta
    friction_events: List[str]
    satisfaction_score: float  # 1-5 scale

class UsabilitySimulator:
    """Simulates user tasks and measures usability."""
    
    def __init__(self, seed: Optional[int] = None):
        """Initialize with optional seed for reproducibility."""
        self.rng = random.Random(seed)
        
        # Define common tasks
        self._task_templates = {
            TaskType.LOGIN: Task(
                type=TaskType.LOGIN,
                user="",  # Filled at runtime
                device="",  # Filled at runtime
                requires_mfa=True,
                expected_duration=timedelta(seconds=30)
            ),
            TaskType.ACCESS_FILE: Task(
                type=TaskType.ACCESS_FILE,
                user="",
                device="",
                resource="/app/files",
                requires_mfa=False,
                expected_duration=timedelta(minutes=1)
            ),
            TaskType.EDIT_FILE: Task(
                type=TaskType.EDIT_FILE,
                user="",
                device="",
                resource="/app/files",
                requires_mfa=False,
                expected_duration=timedelta(minutes=10)
            ),
            TaskType.RUN_REPORT: Task(
                type=TaskType.RUN_REPORT,
                user="",
                device="",
                resource="/app/db",
                requires_mfa=True,
                expected_duration=timedelta(minutes=5)
            ),
            TaskType.ADMIN_TASK: Task(
                type=TaskType.ADMIN_TASK,
                user="",
                device="",
                resource="/app/admin",
                requires_mfa=True,
                expected_duration=timedelta(minutes=15)
            )
        }
    
    def _generate_task(self, user: str, device: str, task_type: Optional[TaskType] = None) -> Task:
        """Generate a random task for a user."""
        if task_type is None:
            task_type = self.rng.choice(list(TaskType))
        
        template = self._task_templates[task_type]
        return Task(
            type=template.type,
            user=user,
            device=device,
            resource=template.resource,
            requires_mfa=template.requires_mfa,
            expected_duration=template.expected_duration
        )
    
    def _simulate_task_attempt(
        self,
        task: Task,
        controls_enabled: bool
    ) -> TaskResult:
        """Simulate a single task attempt."""
        friction_events = []
        
        # Base duration is expected +/- 20%
        base_duration = task.expected_duration.total_seconds()
        variance = base_duration * 0.2
        duration = timedelta(
            seconds=base_duration + self.rng.uniform(-variance, variance)
        )
        
        if controls_enabled:
            # Add MFA friction if required
            if task.requires_mfa:
                friction_events.append("mfa_prompt")
                duration += timedelta(seconds=self.rng.uniform(10, 30))
            
            # Random device posture check
            if self.rng.random() < 0.1:
                friction_events.append("posture_check")
                duration += timedelta(seconds=self.rng.uniform(30, 120))
            
            # Random session timeout
            if self.rng.random() < 0.05:
                friction_events.append("session_timeout")
                duration += timedelta(seconds=self.rng.uniform(30, 60))
        
        # Calculate satisfaction (1-5 scale)
        base_satisfaction = 4.0  # Start with good satisfaction
        
        # Reduce satisfaction for friction events
        satisfaction = base_satisfaction - (len(friction_events) * 0.5)
        
        # Reduce satisfaction if task takes longer than expected
        if duration > task.expected_duration * 1.5:
            satisfaction -= 1.0
        
        # Ensure satisfaction stays in range
        satisfaction = max(1.0, min(5.0, satisfaction))
        
        return TaskResult(
            task=task,
            success=True,  # For now, assume tasks eventually succeed
            duration=duration,
            friction_events=friction_events,
            satisfaction_score=satisfaction
        )
    
    def simulate_workday(
        self,
        user: str,
        device: str,
        task_count: int,
        controls_enabled: bool = True
    ) -> List[TaskResult]:
        """
        Simulate a user's workday.
        
        Args:
            user: Username
            device: Device ID
            task_count: Number of tasks to simulate
            controls_enabled: Whether ZTA controls are enabled
            
        Returns:
            List of task results
        """
        results = []
        
        # Always start with login
        login_task = self._generate_task(user, device, TaskType.LOGIN)
        results.append(self._simulate_task_attempt(login_task, controls_enabled))
        
        # Generate random tasks for the day
        for _ in range(task_count - 1):
            task = self._generate_task(user, device)
            results.append(self._simulate_task_attempt(task, controls_enabled))
        
        return results

def calculate_sus_score(results: List[TaskResult]) -> float:
    """
    Calculate a System Usability Scale (SUS) like score.
    
    Args:
        results: List of task results
        
    Returns:
        SUS score (0-100)
    """
    if not results:
        return 0.0
    
    # Convert satisfaction scores (1-5) to SUS-like scores (0-100)
    scores = [r.satisfaction_score * 20 for r in results]
    return sum(scores) / len(scores)
