import sys
import time
import threading
import pythoncom
from backend.core.activation import ActivationManager
from backend.core.tray import start_tray_thread
from frontend.overlay.window import OverlayWindow
from backend.core.agent import Agent
from backend.core.os_context import get_open_explorer_windows
from backend.tasks.organise_folder import OrganiseFolderTask
from backend.tasks.find_file import FindFileTask
from backend.tasks.change_cursor import ChangeCursorTask
from backend.core.action_log import action_log

def main():
    print("CursorOS booting...")
    
    agent = Agent()
    overlay = None
    
    def on_submit(text):
        print(f"User query: {text}")
        
        def process_task():
            # Initialize COM for this thread
            pythoncom.CoInitialize()
            try:
                # 1. Gather Context
                context = {
                    "explorer_windows": get_open_explorer_windows()
                }
                
                # 2. Think
                print("Agent is thinking...")
                plan = agent.think(text, context)
                print(f"Plan: {plan}")
                
                action = plan.get("action")
                params = plan.get("params", {})
                explanation = plan.get("explanation", "Executing your request.")
                
                # 3. Execute Task
                if action == "organise_folder":
                    path = params.get("path")
                    if path:
                        task = OrganiseFolderTask()
                        log, msg = task.run(path)
                        action_log.add_entry("organise_folder", "executed", {"path": path, "log": log})
                        print(msg)
                    else:
                        print("No path provided for organisation.")
                        
                elif action == "find_file":
                    desc = params.get("description")
                    if desc:
                        task = FindFileTask()
                        results, msg = task.run(desc)
                        action_log.add_entry("find_file", "executed", {"description": desc, "results": results})
                        print(msg)
                        if results:
                            print("Matches found:")
                            for r in results:
                                print(f" - {r}")
                            
                elif action == "change_cursor":
                    desc = params.get("description")
                    if desc:
                        task = ChangeCursorTask()
                        success, msg = task.run(desc)
                        action_log.add_entry("change_cursor", "executed", {"description": desc, "success": success})
                        print(msg)
                        
                elif action == "clarify":
                    question = params.get("question", "Could you please clarify?")
                    print(f"Agent asks: {question}")
                    
            except Exception as e:
                print(f"Error in background task: {e}")
            finally:
                # Clean up COM
                pythoncom.CoUninitialize()

        # Start processing in a background thread
        threading.Thread(target=process_task, daemon=True).start()

    def trigger_overlay():
        nonlocal overlay
        print("Activation hook fired!")
        if overlay:
            overlay.root.after(0, overlay.show)
        else:
            print("Overlay not initialized yet.")

    activation_mgr = ActivationManager(on_activate_callback=trigger_overlay)
    activation_mgr.register_hotkey()
    
    def quit_callback():
        print("Quitting CursorOS...")
        sys.exit(0)
        
    start_tray_thread(on_activate=trigger_overlay, on_quit=quit_callback)
    
    overlay = OverlayWindow(on_submit=on_submit)
    
    print("CursorOS is running. Press Ctrl+Shift+Space to activate.")
    overlay.run()

if __name__ == "__main__":
    main()
