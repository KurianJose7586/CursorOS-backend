import pytest
from unittest.mock import MagicMock, patch
from backend.core.agent import Agent

@patch('backend.core.llm.llm_service.call')
def test_agent_think_success(mock_llm_call):
    # Setup mock
    mock_llm_call.return_value = {
        "action": "organise_folder", 
        "params": {"path": "C:\\Downloads"}, 
        "explanation": "I will organize your downloads folder."
    }
    
    agent = Agent()
    context = {"explorer_windows": [{"title": "Downloads", "path": "C:\\Downloads"}]}
    result = agent.think("organize my downloads", context)
    
    assert result["action"] == "organise_folder"
    assert result["params"]["path"] == "C:\\Downloads"
    assert "explanation" in result

@patch('backend.core.llm.llm_service.call')
def test_agent_think_error_fallback(mock_llm_call):
    mock_llm_call.side_effect = Exception("API Error")
    
    agent = Agent()
    result = agent.think("do something", {})
    
    assert result["action"] == "clarify"
    assert "error" in result["params"]["question"].lower()
