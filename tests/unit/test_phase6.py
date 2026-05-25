import pytest
import os
from unittest.mock import MagicMock, patch
from backend.tasks.find_file import FindFileTask

@patch('backend.core.llm.llm_service.call')
def test_find_file_programmatic(mock_llm_call):
    # Setup mock API for Intent Parser 2.0
    mock_llm_call.return_value = {
        "keywords": ["report", "2024"],
        "extensions": [".pdf"],
        "temporal_hint": None,
        "semantic_intent": "document",
        "confidence": 1.0
    }
    
    task = FindFileTask()
    
    # Mock retrieval methods to bypass real system calls
    task._retrieve_windows_index = MagicMock(return_value=["C:\\Docs\\report_2024.pdf"])
    task._retrieve_active_context = MagicMock(return_value=[])
    task._retrieve_recent_items = MagicMock(return_value=[])
    
    results, msg = task.run("find my 2024 report pdf")
    
    assert "Found" in msg
    assert any("report_2024.pdf" in r for r in results)
