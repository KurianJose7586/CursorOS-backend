import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from backend.tasks.change_cursor import ChangeCursorTask

def test_change_cursor_search_and_download(tmp_path):
    with patch('requests.get') as mock_get:
        # Setup mock download
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b"data"]
        mock_get.return_value = mock_response
        
        task = ChangeCursorTask()
        task.cursor_dir = tmp_path
        
        url = task.search_cursor("blue arrow")
        assert url is not None
        
        path = task.download_cursor("https://real-url.com/c.cur")
        assert path.exists()
        assert path.name == "new_cursor.cur"

def test_change_cursor_run_success():
    task = ChangeCursorTask()
    # Mocking internal methods for the run test
    task.search_cursor = MagicMock(return_value="http://url")
    task.download_cursor = MagicMock(return_value=Path("mock.cur"))
    task.apply_cursor = MagicMock()
    
    success, msg = task.run("test cursor")
    assert success is True
    assert "Applied" in msg
    task.apply_cursor.assert_called_once()
