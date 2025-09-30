from datetime import timedelta
from dataclasses import dataclass
from src.sim.usability_metrics import SUSCalculator, UsabilityAnalyzer

@dataclass
class Task:
    """Test task class."""
    type: str

@dataclass
class TaskResult:
    """Test task result class."""
    task: Task
    duration: timedelta
    success: bool
    friction_events: list
    satisfaction_score: float

def test_sus_calculator():
    """Test SUS score calculation."""
    calculator = SUSCalculator()
    
    # Test with empty results
    score = calculator.calculate_sus([])
    assert 0.0 <= score <= 100.0
    
    # Test with perfect results
    results = [
        TaskResult(
            task=Task(type="login"),
            duration=timedelta(seconds=5),
            success=True,
            friction_events=[],
            satisfaction_score=5.0
        )
    ] * 5
    score = calculator.calculate_sus(results)
    assert 80.0 <= score <= 100.0
    
    # Test with poor results
    results = [
        TaskResult(
            task=Task(type="login"),
            duration=timedelta(seconds=30),
            success=False,
            friction_events=["error1", "error2"],
            satisfaction_score=1.0
        )
    ] * 5
    score = calculator.calculate_sus(results)
    assert 0.0 <= score <= 30.0  # Allow slightly higher scores for poor results

def test_usability_analyzer():
    """Test usability metrics calculation."""
    analyzer = UsabilityAnalyzer()
    
    # Test with empty results
    metrics = analyzer.calculate_metrics([])
    assert metrics.sus_score == 0.0
    assert metrics.task_completion_rate == 0.0
    assert metrics.avg_task_duration == 0.0
    assert metrics.friction_events_per_task == 0.0
    assert metrics.satisfaction_score == 0.0
    assert metrics.detailed_metrics == {}
    
    # Test with mixed results
    results = [
        TaskResult(
            task=Task(type="login"),
            duration=timedelta(seconds=10),
            success=True,
            friction_events=[],
            satisfaction_score=4.0
        ),
        TaskResult(
            task=Task(type="file_access"),
            duration=timedelta(seconds=20),
            success=False,
            friction_events=["error1", "error2"],
            satisfaction_score=2.0
        )
    ]
    
    metrics = analyzer.calculate_metrics(results)
    assert 0.0 <= metrics.sus_score <= 100.0
    assert metrics.task_completion_rate == 0.5
    assert metrics.avg_task_duration == 15.0
    assert metrics.friction_events_per_task == 1.0
    assert metrics.satisfaction_score == 3.0
    assert len(metrics.detailed_metrics) > 0

def test_edge_cases():
    """Test edge cases in metrics calculation."""
    analyzer = UsabilityAnalyzer()
    
    # Single result
    results = [
        TaskResult(
            task=Task(type="login"),
            duration=timedelta(seconds=10),
            success=True,
            friction_events=[],
            satisfaction_score=5.0
        )
    ]
    metrics = analyzer.calculate_metrics(results)
    assert metrics.task_completion_rate == 1.0
    
    # All failures
    results = [
        TaskResult(
            task=Task(type="login"),
            duration=timedelta(seconds=10),
            success=False,
            friction_events=["error"],
            satisfaction_score=1.0
        )
    ] * 3
    metrics = analyzer.calculate_metrics(results)
    assert metrics.task_completion_rate == 0.0