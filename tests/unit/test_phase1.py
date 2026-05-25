import pytest
from backend.core.activation import ActivationManager

def test_hotkey_registration():
    """Test that the hotkey registration function does not raise an exception."""
    def dummy_callback():
        pass
    
    mgr = ActivationManager(on_activate_callback=dummy_callback)
    try:
        mgr.register_hotkey()
    except Exception as e:
        pytest.fail(f"Hotkey registration raised exception: {e}")

def test_activation_hook_callable():
    """Test that the activation signal hook is callable."""
    called = False
    def dummy_callback():
        nonlocal called
        called = True
    
    mgr = ActivationManager(on_activate_callback=dummy_callback)
    mgr.handle_activation()
    assert called is True
