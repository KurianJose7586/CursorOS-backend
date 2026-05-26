import json
from backend.core.llm import llm_service

class Agent:
    def think(self, user_query: str, context: dict) -> dict:
        system_prompt = """You are CursorOS, a Windows desktop AI overlay agent.
Your objective is to provide a plan consisting of one or more actions to fulfill the user's request.

CRITICAL JSON STRUCTURE:
You must return ONLY a JSON object with a single key "actions", containing a list of action objects.
Structure: {{ "actions": [ {{ "action": "...", "params": {{...}}, "explanation": "..." }} ] }}

AVAILABLE ACTIONS:
1. find_file: Finds a path. Params: {{ "description": str }}.
2. organise_folder: Groups files into subfolders. Params: {{ "path": str }}.
3. open_path: Launches a file/folder. Params: {{ "path": str }}.
4. chat: Talks to the user. Params: {{ "message": str }}. Use for greetings/questions.
5. change_cursor: Changes mouse icon. Params: {{ "description": str }}.
6. clarify: Asks for more info. Params: {{ "question": str }}.

EXAMPLES:
- User: "hello"
  Response: {{ "actions": [ {{ "action": "chat", "params": {{ "message": "Hello! I am CursorOS. How can I help you manage your files today?" }}, "explanation": "Greeting the user." }} ] }}

- User: "find my resume and open it"
  Response: {{ "actions": [ {{ "action": "find_file", "params": {{ "description": "resume" }}, "explanation": "Locating your resume file." }}, {{ "action": "open_path", "params": {{ "path": null }}, "explanation": "Opening the found file." }} ] }}

CONTEXT:
Open Explorer Windows: {explorer_windows}
"""
        explorer_windows = context.get("explorer_windows", [])
        formatted_system_prompt = system_prompt.format(explorer_windows=json.dumps(explorer_windows))
        
        try:
            print("DEBUG: Requesting plan from AI...")
            result = llm_service.call(formatted_system_prompt, f"User Query: {user_query}")
            
            # Ensure we always return the actions list format
            if "actions" not in result:
                if "action" in result:
                    # Auto-migration for legacy format
                    return {"actions": [result]}
                return {"actions": []}
            return result
            
        except Exception as e:
            print(f"DEBUG: Agent thinking failed: {e}")
            return {
                "actions": [{
                    "action": "chat",
                    "params": {"message": f"I hit a technical snag while thinking: {str(e)}"},
                    "explanation": "Error fallback."
                }]
            }
