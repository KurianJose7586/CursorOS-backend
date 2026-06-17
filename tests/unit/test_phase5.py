import pytest
import os
from unittest.mock import MagicMock, patch
from backend.tasks.organise_folder import OrganiseFolderTask

@patch('backend.core.llm.llm_service.call')
def test_organise_folder_rollback(mock_llm_call, tmp_path):
    # Setup mock to propose two folders
    mock_llm_call.return_value = {
        "subfolders": [
            {"name": "Folder1", "files": ["file1.txt"]}, 
            {"name": "Folder2", "files": ["file2.txt"]}
        ]
    }
    
    # Create test files
    f1 = tmp_path / "file1.txt"
    f2 = tmp_path / "file2.txt"
    f1.write_text("data1")
    f2.write_text("data2")
    
    task = OrganiseFolderTask()
    
    # Patch shutil.move to fail on the second file
    import shutil
    original_move = shutil.move
    
    def side_effect(src, dst):
        if "file2.txt" in str(src):
            raise IOError("Simulated failure")
        return original_move(src, dst)
        
    with patch('shutil.move', side_effect=side_effect):
        log, msg = task.run(str(tmp_path))
        
    assert "Error" in msg
    # Verify rollback: file1.txt should be back in root, Folder1 should be gone (if empty)
    assert (tmp_path / "file1.txt").exists()
    assert (tmp_path / "file2.txt").exists()
    assert not (tmp_path / "Folder1").exists()
    assert not (tmp_path / "Folder2").exists()
