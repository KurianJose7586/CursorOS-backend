import threading

class ApiBridge:
    def __init__(self, on_submit_callback):
        self.on_submit_callback = on_submit_callback

    def submit_query(self, text):
        """Called from React frontend."""
        print(f"JS -> Python: Query received: {text}")
        if self.on_submit_callback:
            # Run in a separate thread to not block the webview UI
            threading.Thread(target=self.on_submit_callback, args=(text,), daemon=True).start()
        return {"status": "ok"}
