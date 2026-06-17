import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from backend.tasks.change_cursor import ChangeCursorTask

def test_change_cursor_validation(tmp_path):
    task = ChangeCursorTask()
    
    # Valid .cur header
    cur_path = tmp_path / "test.cur"
    cur_path.write_bytes(b'\x00\x00\x02\x00' + b'junk')
    assert task.validate_cursor(cur_path) is True
    
    # Valid .ani (RIFF) header
    ani_path = tmp_path / "test.ani"
    ani_path.write_bytes(b'RIFF' + b'junk')
    assert task.validate_cursor(ani_path) is True
    
    # Invalid header
    bad_path = tmp_path / "test.txt"
    bad_path.write_bytes(b'MZ' + b'junk') # .exe header
    assert task.validate_cursor(bad_path) is False

@patch('winreg.OpenKey')
@patch('winreg.SetValueEx')
@patch('ctypes.windll.user32.SystemParametersInfoW')
def test_change_cursor_apply(mock_spi, mock_set_val, mock_open_key):
    task = ChangeCursorTask()
    path = Path("C:/test.cur")
    
    task.apply_cursor(path)
    
    # Verify registry was called
    mock_set_val.assert_called_once()
    assert mock_set_val.call_args[0][1] == "Arrow"
    assert mock_spi.called is True

def test_change_cursor_download_invalid(tmp_path):
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b"MZ_NOT_A_CURSOR"]
        mock_get.return_value = mock_response
        
        task = ChangeCursorTask()
        task.cursor_dir = tmp_path
        
        with pytest.raises(ValueError, match="security validation"):
            task.download_cursor("https://bad.com/file.cur")
