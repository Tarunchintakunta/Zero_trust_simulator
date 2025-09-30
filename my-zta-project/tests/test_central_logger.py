import json
import threading
from pathlib import Path
from src.logging.central_logger import get_logger

def test_basic_logging(tmp_path):
    """Test basic event logging."""
    log_file = tmp_path / "test.jsonl"
    logger = get_logger(jsonl_path=log_file)

    event = {
        "event_type": "test",
        "message": "hello world"
    }
    logger.log_event(event)
    logger.flush()

    text = log_file.read_text()
    assert "hello world" in text
    assert "test" in text

def test_multiple_sinks(tmp_path):
    """Test logging to multiple sinks."""
    jsonl_file = tmp_path / "test.jsonl"
    csv_file = tmp_path / "test.csv"
    logger = get_logger(jsonl_path=jsonl_file, csv_path=csv_file)

    event = {
        "event_type": "test",
        "message": "hello world"
    }
    logger.log_event(event)
    logger.flush()

    # Check JSONL output
    jsonl_text = jsonl_file.read_text()
    assert "hello world" in jsonl_text

    # Check CSV output
    csv_text = csv_file.read_text()
    assert "event_type" in csv_text
    assert "message" in csv_text
    assert "hello world" in csv_text

def test_rotating_sink(tmp_path):
    """Test rotating log sink."""
    rotating_dir = tmp_path / "logs"
    logger = get_logger(rotating_dir=rotating_dir)

    # Log some events
    for i in range(3):
        event = {
            "event_type": "test",
            "message": f"event {i}"
        }
        logger.log_event(event)
    logger.flush()

    # Should have created at least one log file
    log_files = list(rotating_dir.glob("*.jsonl"))
    assert len(log_files) >= 1

def test_concurrent_logging(tmp_path):
    """Test concurrent logging from multiple threads."""
    log_file = tmp_path / "concurrent.jsonl"
    logger = get_logger(jsonl_path=log_file)

    def worker(i):
        for j in range(10):
            event = {
                "event_type": "test",
                "worker": i,
                "message": f"event {j}"
            }
            logger.log_event(event)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    logger.flush()

    # Load and check events
    events = []
    with open(log_file) as f:
        for line in f:
            events.append(json.loads(line))

    assert len(events) == 50  # 5 workers * 10 events each
    worker_ids = {e["worker"] for e in events}
    assert worker_ids == {0, 1, 2, 3, 4}