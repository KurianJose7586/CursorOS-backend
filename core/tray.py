import pystray
from PIL import Image
import threading
import sys

class TrayManager:
    def __init__(self, on_activate, on_quit):
        self.on_activate = on_activate
        self.on_quit = on_quit
        self.icon = None

    def _create_menu(self):
        return pystray.Menu(
            pystray.MenuItem("Activate", self.on_activate),
            pystray.MenuItem("Quit", self._quit)
        )

    def _quit(self, icon, item):
        self.icon.stop()
        if self.on_quit:
            self.on_quit()

    def run(self):
        image = Image.open("backend/assets/icon.png")
        self.icon = pystray.Icon("CursorOS", image, "CursorOS", self._create_menu())
        self.icon.run()

def start_tray_thread(on_activate, on_quit):
    tray = TrayManager(on_activate, on_quit)
    tray_thread = threading.Thread(target=tray.run, daemon=True)
    tray_thread.start()
    return tray
