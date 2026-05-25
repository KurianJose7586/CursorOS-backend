import json
from backend.core.llm import llm_service

class Agent:
    def think(self, user_query: str, context: dict) -> dict:
        system_prompt = """You are CursorOS, a Windows desktop AI overlay agent.
Your goal is to decide a sequence of actions (a chain) to fulfill the user's request.

AVAILABLE ACTIONS:
1. find_file: Params: {{ "description": str }}. Finds a file/folder path. REQUIRED if you don't have a path yet.
2. organise_folder: Params: {{ "path": str }}. Organizes a folder.
3. open_path: Params: {{ "path": str }}. Opens a file or folder.
4. change_cursor: Params: {{ "description": str }}.
5. clarify: Params: {{ "question": str }}.

CHAINING LOGIC:
- You must return an object with an "actions" key, which is a LIST of action objects.
- If the user wants to do something to a file they haven't specified a path for, use 'find_file' first.
- Example: "find my resume and open it" -> actions: [{"action": "find_file", ...}, {"action": "open_path", ...}]

CONSTRAINTS:
- ONLY return a JSON object with: { "actions": [ { "action", "params", "explanation" } ] }.
- If 'find_file' is part of a chain, leave the "path" param of subsequent actions as null; it will be filled automatically.

CONTEXT:
Open Explorer Windows: {explorer_windows}
"""
        explorer_windows = context.get("explorer_windows", [])
        formatted_system_prompt = system_prompt.format(explorer_windows=json.dumps(explorer_windows))
        
        try:
            return llm_service.call(formatted_system_prompt, f"User Query: {user_query}")
        except Exception as e:
            return {
                "actions": [{
                    "action": "clarify",
                    "params": {"question": f"Error: {str(e)}"},
                    "explanation": "I encountered an error while thinking."
                }]
            }
