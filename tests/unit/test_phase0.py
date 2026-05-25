import pytest
from backend.config.settings import settings

def test_settings_load():
    """Verify config/settings.py loads and has expected attributes."""
    assert hasattr(settings, "HOTKEY")
    assert hasattr(settings, "PRIMARY_MODEL")
    assert hasattr(settings, "FALLBACK_MODEL")

def test_missing_api_keys_assertion():
    """Verify that settings can be accessed if at least one key is present."""
    # This is hard to test once the module is loaded and raises ValueError
    # But we can check if the current settings object has what we expect
    assert settings.GOOGLE_API_KEY is not None or settings.GROQ_API_KEY is not None
