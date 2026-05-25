import pytest
import os
from backend.core.os_context import get_directory_contents

def test_get_directory_contents_real_dir(tmp_path):
    """Test get_directory_contents with a temporary directory."""
    # Create some files
    (tmp_path / "file1.txt").write_text("hello")
    (tmp_path / "subdir").mkdir()
    (tmp_path / "file2.py").write_text("print('hi')")
    
    items, truncated = get_directory_contents(str(tmp_path))
    
    assert len(items) == 3
    assert not truncated
    
    names = [item['name'] for item in items]
    assert "file1.txt" in names
    assert "subdir" in names
    assert "file2.py" in names
    
    # Check types
    for item in items:
        if item['name'] == "subdir":
            assert item['type'] == "folder"
        else:
            assert item['type'] == "file"

def test_get_directory_contents_truncation(tmp_path):
    """Test truncation logic."""
    for i in range(250):
        (tmp_path / f"file{i}.txt").write_text("test")
        
    items, truncated = get_directory_contents(str(tmp_path))
    assert len(items) == 200
    assert truncated is True

def test_get_directory_contents_non_existent():
    """Test handling of non-existent path."""
    with pytest.raises(FileNotFoundError):
        get_directory_contents("C:\\non_existent_path_xyz")
