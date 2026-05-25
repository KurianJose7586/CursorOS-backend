import json
from backend.core.llm import llm_service

class Agent:
    def think(self, user_query: str, context: dict) -> dict:
        system_prompt = """You are CursorOS, a Windows desktop AI overlay agent.
Your goal is to decide the best action to take based on the user's query and the current OS context.

AVAILABLE ACTIONS:
1. organise_folder: Params: {{ "path": str }}. Use this if the user wants to organize files in a directory.
2. find_file: Params: {{ "description": str }}. Use this if the user is looking for a specific file.
3. change_cursor: Params: {{ "description": str }}. Use this if the user wants to change their mouse cursor.
4. clarify: Params: {{ "question": str }}. Use this if the user's intent is unclear or if more information is needed.

CONSTRAINTS:
- You must ONLY return a JSON object with the following keys: "action", "params", "explanation".
- Choose exactly one action.
- The explanation should be a brief sentence for the user.

CONTEXT:
Open Explorer Windows: {explorer_windows}
"""
        explorer_windows = context.get("explorer_windows", [])
        formatted_system_prompt = system_prompt.format(explorer_windows=json.dumps(explorer_windows))
        
        try:
            return llm_service.call(formatted_system_prompt, f"User Query: {user_query}")
        except Exception as e:
            return {
                "action": "clarify",
                "params": {"question": f"Error: {str(e)}"},
                "explanation": "I encountered an error while thinking."
            }
