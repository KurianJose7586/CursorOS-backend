import pytest
import os
import json
from backend.core.action_log import ActionLog

def test_action_log_persistence(tmp_path):
    log_file = tmp_path / "test_log.json"
    logger = ActionLog(log_path=str(log_file))
    
    logger.add_entry("test_task", "test_action", "test_detail")
    
    # Verify file exists and has content
    assert log_file.exists()
    with open(log_file, "r") as f:
        data = json.load(f)
        assert len(data) == 1
        assert data[0]["task"] == "test_task"

def test_action_log_reload(tmp_path):
    log_file = tmp_path / "test_log.json"
    logger1 = ActionLog(log_path=str(log_file))
    logger1.add_entry("task1", "action1", "detail1")
    
    logger2 = ActionLog(log_path=str(log_file))
    assert len(logger2.log) == 1
    assert logger2.get_last_action()["task"] == "task1"
