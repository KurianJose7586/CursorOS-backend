import keyboard
from backend.config.settings import settings

class ActivationManager:
    def __init__(self, on_activate_callback):
        self.on_activate_callback = on_activate_callback

    def register_hotkey(self):
        keyboard.add_hotkey(settings.HOTKEY, self.handle_activation)
        print(f"Hotkey {settings.HOTKEY} registered.")

    def handle_activation(self):
        print("Agent activated via hotkey")
        if self.on_activate_callback:
            self.on_activate_callback()

def default_activation_hook():
    print("Activation hook fired!")
