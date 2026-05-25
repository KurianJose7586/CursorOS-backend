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
    
    def on_select(path):
        print(f"Opening: {path}")
        try:
            os.startfile(path)
            overlay.root.after(0, overlay.hide)
        except Exception as e:
            print(f"Error opening file: {e}")

    def on_submit(text):
        print(f"User query: {text}")
        
        # 0. UI Setup for Planning
        overlay.root.after(0, lambda: overlay.add_task_step("plan", "Agentic Planning"))

        def process_chain():
            pythoncom.CoInitialize()
            try:
                # 1. Gather Context & Plan
                overlay.root.after(0, lambda: overlay.update_task_status("plan", "in-progress"))
                context = {"explorer_windows": get_open_explorer_windows()}
                plan = agent.think(text, context)
                actions = plan.get("actions", [])
                overlay.root.after(0, lambda: overlay.update_task_status("plan", "completed"))
                
                last_result_path = None
                
                # 2. Sequential Execution
                for i, action_item in enumerate(actions):
                    action = action_item.get("action")
                    params = action_item.get("params", {})
                    explanation = action_item.get("explanation", "Executing...")
                    
                    # Add dynamic UI step
                    task_id = f"task_{i}"
                    overlay.root.after(0, lambda d=explanation: overlay.add_task_step(task_id, d))
                    overlay.root.after(0, lambda: overlay.update_task_status(task_id, "in-progress"))
                    
                    try:
                        if action == "find_file":
                            desc = params.get("description")
                            task = FindFileTask()
                            results, msg = task.run(desc)
                            if results:
                                last_result_path = results[0] # Take the top match for the chain
                                # If it's the LAST action, show results in UI
                                if i == len(actions) - 1:
                                    overlay.root.after(0, lambda r=results: overlay.display_results(r))
                            else:
                                raise Exception(f"Could not find '{desc}'")
                                
                        elif action == "organise_folder":
                            # Use path from params or from previous find_file
                            path = params.get("path") or last_result_path
                            if not path: raise Exception("No path provided for organization.")
                            task = OrganiseFolderTask()
                            log, msg = task.run(path)
                            action_log.add_entry("organise_folder", "executed", {"path": path, "log": log})
                            
                        elif action == "open_path":
                            path = params.get("path") or last_result_path
                            if not path: raise Exception("No path provided to open.")
                            on_select(path) # Re-use the existing launch logic
                            
                        elif action == "change_cursor":
                            desc = params.get("description")
                            task = ChangeCursorTask()
                            task.run(desc)
                            
                        overlay.root.after(0, lambda: overlay.update_task_status(task_id, "completed"))
                        
                    except Exception as e:
                        print(f"Action '{action}' failed: {e}")
                        overlay.root.after(0, lambda: overlay.update_task_status(task_id, "failed"))
                        break # Stop the chain on failure

                # Auto-hide after short delay if not displaying results
                if actions and actions[-1].get("action") != "find_file":
                    time.sleep(2)
                    overlay.root.after(0, overlay.hide)

            except Exception as e:
                print(f"Error in chain: {e}")
                overlay.root.after(0, lambda: overlay.update_task_status("plan", "failed"))
            finally:
                pythoncom.CoUninitialize()

        threading.Thread(target=process_chain, daemon=True).start()

    def trigger_overlay():
        nonlocal overlay
        print("Activation hook fired!")
        if overlay:
            overlay.root.after(0, overlay.show)
        else:
            print("Overlay not initialized yet.")
    
    # ... rest of main initialization ...
    activation_mgr = ActivationManager(on_activate_callback=trigger_overlay)
    activation_mgr.register_hotkey()
    
    def quit_callback():
        print("Quitting CursorOS...")
        sys.exit(0)
        
    start_tray_thread(on_activate=trigger_overlay, on_quit=quit_callback)
    
    overlay = OverlayWindow(on_submit=on_submit, on_select=on_select)
    
    print("CursorOS is running. Press Ctrl+Shift+Space to activate.")
    overlay.run()

if __name__ == "__main__":
    main()
