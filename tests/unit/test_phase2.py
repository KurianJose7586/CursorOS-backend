import pytest
from unittest.mock import MagicMock, patch
from frontend.overlay.window import OverlayWindow

@patch('tkinter.Tk')
@patch('tkinter.Frame')
@patch('tkinter.Entry')
@patch('tkinter.Label')
@patch('tkinter.StringVar')
def test_overlay_init(mock_stringvar, mock_label, mock_entry, mock_frame, mock_tk):
    """Test that the overlay window initialises without error."""
    def dummy_callback(*args, **kwargs):
        pass
    
    mock_root = MagicMock()
    mock_tk.return_value = mock_root
    
    overlay = OverlayWindow(on_submit=dummy_callback, on_select=dummy_callback, on_execute=dummy_callback)
    assert overlay.root == mock_root
    assert overlay.entry is not None
    mock_tk.assert_called_once()

@patch('tkinter.Tk')
@patch('tkinter.Frame')
@patch('tkinter.Entry')
@patch('tkinter.Label')
@patch('tkinter.StringVar')
def test_overlay_hide(mock_stringvar, mock_label, mock_entry, mock_frame, mock_tk):
    """Test that the hide method resets the UI and starts animation."""
    def dummy_callback(*args, **kwargs):
        pass
    
    mock_root = MagicMock()
    mock_tk.return_value = mock_root
    
    # Mock after to call the callback immediately to bypass animation delays
    def mock_after(ms, func, *args):
        if func:
            func()
    mock_root.after.side_effect = mock_after
    
    mock_entry_instance = MagicMock()
    mock_entry.return_value = mock_entry_instance
    
    mock_header = MagicMock()
    # In __init__, header is the first frame packed after outer_border and container
    # But it's easier to just mock the call to pack_forget on any frame
    
    overlay = OverlayWindow(on_submit=dummy_callback, on_select=dummy_callback, on_execute=dummy_callback)
    
    # We need to ensure header is tracked
    overlay.header = MagicMock()
    
    overlay.show()
    overlay.hide()
    
    # Check that header was hidden
    overlay.header.pack_forget.assert_called()
    # Check that entry was cleared (this happens at the end of animation in our mock)
    mock_entry_instance.delete.assert_called()
