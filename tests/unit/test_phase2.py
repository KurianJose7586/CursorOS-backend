import pytest
from unittest.mock import MagicMock, patch
from frontend.overlay.window import OverlayWindow

@patch('tkinter.Tk')
@patch('tkinter.Frame')
@patch('tkinter.Entry')
@patch('tkinter.Button')
def test_overlay_init(mock_button, mock_entry, mock_frame, mock_tk):
    """Test that the overlay window initialises without error."""
    def dummy_submit(text):
        pass
    
    mock_root = MagicMock()
    mock_tk.return_value = mock_root
    
    overlay = OverlayWindow(on_submit=dummy_submit)
    assert overlay.root == mock_root
    assert overlay.entry is not None
    mock_tk.assert_called_once()

@patch('tkinter.Tk')
@patch('tkinter.Frame')
@patch('tkinter.Entry')
@patch('tkinter.Button')
def test_overlay_hide(mock_button, mock_entry, mock_frame, mock_tk):
    """Test that the hide method withdraws the window."""
    def dummy_submit(text):
        pass
    
    mock_root = MagicMock()
    mock_tk.return_value = mock_root
    
    mock_entry_instance = MagicMock()
    mock_entry.return_value = mock_entry_instance
    
    overlay = OverlayWindow(on_submit=dummy_submit)
    overlay.show()
    overlay.hide()
    
    # Check that withdraw was called
    mock_root.withdraw.assert_called()
    # Check that entry was cleared
    # Note: tkinter.END is usually "end". In our code we use tk.END.
    mock_entry_instance.delete.assert_called()
