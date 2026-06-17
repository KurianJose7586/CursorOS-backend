import keyboard
import time
from backend.config.settings import settings

class ActivationManager:
    def __init__(self, on_activate_callback):
        self.on_activate_callback = on_activate_callback
        self.last_trigger_time = 0
        self.cooldown = 0.5 # seconds

    def register_hotkey(self):
        keyboard.add_hotkey(settings.HOTKEY, self.handle_activation)
        print(f"Hotkey {settings.HOTKEY} registered.")

    def handle_activation(self):
        current_time = time.time()
        if current_time - self.last_trigger_time < self.cooldown:
            return
            
        self.last_trigger_time = current_time
        print("Agent activated via hotkey")
        if self.on_activate_callback:
            self.on_activate_callback()

def default_activation_hook():
    print("Activation hook fired!")
