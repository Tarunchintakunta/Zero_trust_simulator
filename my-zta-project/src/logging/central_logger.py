"""
Zero Trust Architecture (ZTA) Central Logger

This module provides centralized logging functionality for the ZTA simulation
with support for multiple output sinks and rotation.
"""

import csv
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Union


class LogSink(ABC):
    """Abstract base class for log sinks."""

    @abstractmethod
    def write_event(self, event: Dict[str, Any]) -> None:
        """Write a single event."""
        pass

    @abstractmethod
    def flush(self) -> None:
        """Flush any buffered writes."""
        pass


class JSONLSink(LogSink):
    """JSONL file sink."""

    def __init__(self, file_path: Union[str, Path]):
        """Initialize with file path."""
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def write_event(self, event: Dict[str, Any]) -> None:
        """Write event as JSON line."""
        with open(self.file_path, "a") as f:
            f.write(json.dumps(event) + "\n")

    def flush(self) -> None:
        """Nothing to flush for JSONL sink."""
        pass


class CSVSink(LogSink):
    """CSV file sink with header."""

    def __init__(self, file_path: Union[str, Path]):
        """Initialize with file path."""
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._header_written = False

    def write_event(self, event: Dict[str, Any]) -> None:
        """Write event as CSV row."""
        with open(self.file_path, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=event.keys())

            # Write header if needed
            if not self._header_written:
                writer.writeheader()
                self._header_written = True

            writer.writerow(event)

    def flush(self) -> None:
        """Nothing to flush for CSV sink."""
        pass


class RotatingJSONLSink(LogSink):
    """JSONL sink that rotates files by experiment ID."""

    def __init__(self, base_dir: Union[str, Path]):
        """Initialize with base directory."""
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._current_file: Optional[Path] = None

    def set_experiment(self, experiment_id: str) -> None:
        """Set current experiment for rotation."""
        self._current_file = self.base_dir / f"{experiment_id}.jsonl"

    def write_event(self, event: Dict[str, Any]) -> None:
        """Write event to current experiment file."""
        if not self._current_file:
            experiment_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.set_experiment(experiment_id)

        with open(self._current_file, "a") as f:
            f.write(json.dumps(event) + "\n")

    def flush(self) -> None:
        """Nothing to flush for rotating sink."""
        pass


class CentralLogger:
    """Central logging facility for ZTA events."""

    def __init__(self):
        """Initialize with no sinks."""
        self.sinks: List[LogSink] = []

        # Set up Python logging
        self._logger = logging.getLogger(__name__)

    def add_sink(self, sink: LogSink) -> None:
        """Add a log sink."""
        self.sinks.append(sink)

    def remove_sink(self, sink: LogSink) -> None:
        """Remove a log sink."""
        self.sinks.remove(sink)

    def log_event(self, event: Dict[str, Any]) -> None:
        """Log a single event to all sinks."""
        # Ensure timestamp is present
        if "timestamp" not in event:
            event["timestamp"] = datetime.utcnow().isoformat()

        # Write to all sinks
        for sink in self.sinks:
            try:
                sink.write_event(event)
            except Exception as e:
                self._logger.error(f"Failed to write to sink {sink}: {e}")

    def log_events(self, events: List[Dict[str, Any]]) -> None:
        """Log multiple events to all sinks."""
        for event in events:
            self.log_event(event)

    def flush(self) -> None:
        """Flush all sinks."""
        for sink in self.sinks:
            try:
                sink.flush()
            except Exception as e:
                self._logger.error(f"Failed to flush sink {sink}: {e}")


def get_logger(
    jsonl_path: Optional[Union[str, Path]] = None,
    csv_path: Optional[Union[str, Path]] = None,
    rotating_dir: Optional[Union[str, Path]] = None,
) -> CentralLogger:
    """
    Get a logger instance with configured sinks.

    Args:
        jsonl_path: Optional path for JSONL output
        csv_path: Optional path for CSV output
        rotating_dir: Optional directory for rotating JSONL files

    Returns:
        CentralLogger instance
    """
    logger = CentralLogger()

    if jsonl_path:
        logger.add_sink(JSONLSink(jsonl_path))

    if csv_path:
        logger.add_sink(CSVSink(csv_path))

    if rotating_dir:
        logger.add_sink(RotatingJSONLSink(rotating_dir))

    return logger
