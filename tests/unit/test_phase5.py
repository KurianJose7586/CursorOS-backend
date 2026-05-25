import pytest
import os
from unittest.mock import MagicMock, patch
from backend.tasks.organise_folder import OrganiseFolderTask

@patch('backend.core.llm.llm_service.call')
def test_organise_folder_success(mock_llm_call, tmp_path):
    # Setup mock
    mock_llm_call.return_value = {
        "subfolders": [
            {"name": "Images", "files": ["img1.jpg", "img2.png"]}, 
            {"name": "Docs", "files": ["doc1.pdf"]}
        ]
    }
    
    # Create test files
    (tmp_path / "img1.jpg").write_text("data")
    (tmp_path / "img2.png").write_text("data")
    (tmp_path / "doc1.pdf").write_text("data")
    (tmp_path / "other.txt").write_text("data")
    
    task = OrganiseFolderTask()
    log, msg = task.run(str(tmp_path))
    
    assert msg == "Organisation complete."
    assert os.path.exists(tmp_path / "Images" / "img1.jpg")
    assert os.path.exists(tmp_path / "Images" / "img2.png")
    assert os.path.exists(tmp_path / "Docs" / "doc1.pdf")
    assert os.path.exists(tmp_path / "other.txt")
    
    actions = [a["action"] for a in log]
    assert "created_folder" in actions
    assert "moved_file" in actions
