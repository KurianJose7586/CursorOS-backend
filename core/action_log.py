import json
import os
from datetime import datetime

class ActionLog:
    def __init__(self, log_path="backend/assets/session_log.json"):
        self.log_path = log_path
        self.log = []
        self._load_log()

    def _load_log(self):
        if os.path.exists(self.log_path):
            try:
                with open(self.log_path, "r") as f:
                    self.log = json.load(f)
            except Exception as e:
                print(f"Error loading log: {e}")
                self.log = []

    def _save_log(self):
        try:
            with open(self.log_path, "w") as f:
                json.dump(self.log, f, indent=2)
        except Exception as e:
            print(f"Error saving log: {e}")

    def add_entry(self, task, action, detail):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "task": task,
            "action": action,
            "detail": detail
        }
        self.log.append(entry)
        self._save_log()

    def get_last_action(self):
        if self.log:
            return self.log[-1]
        return None

    def clear_log(self):
        self.log = []
        self._save_log()

action_log = ActionLog()
