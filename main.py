import sys
import os
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
    
    # Store current plan state
    current_chain_data = {
        "actions": [],
        "context": {}
    }

    def on_select(path):
        print(f"Opening: {path}")
        try:
            os.startfile(path)
            overlay.root.after(0, overlay.hide)
        except Exception as e:
            print(f"Error opening file: {e}")

    def on_execute():
        """Triggered when user clicks 'Execute Plan' in Plan Mode."""
        print("User confirmed plan. Executing...")
        overlay.action_bar.pack_forget() # Hide the button
        user_text = overlay.entry.get()
        threading.Thread(target=execute_action_chain, args=(current_chain_data["actions"], user_text), daemon=True).start()

    def on_submit(text):
        print(f"User query ({overlay.mode.get()} mode): {text}")
        overlay.root.after(0, lambda: overlay.add_task_step("plan", "Generating Plan"))

        def process_planning():
            pythoncom.CoInitialize()
            try:
                overlay.root.after(0, lambda: overlay.update_task_status("plan", "in-progress"))
                context = {"explorer_windows": get_open_explorer_windows()}
                plan = agent.think(text, context)
                
                actions = plan.get("actions", [])
                if not isinstance(actions, list):
                    raise Exception("Agent 'actions' is not a list.")

                current_chain_data["actions"] = actions
                overlay.root.after(0, lambda: overlay.update_task_status("plan", "completed"))
                
                if overlay.mode.get() == "Plan":
                    # In Plan Mode, show the summary and the Execute button
                    overlay.root.after(0, overlay.show_plan_ready)
                else:
                    # In Auto Mode, execute immediately
                    execute_action_chain(actions, text)

            except Exception as e:
                print(f"Planning Error: {e}")
                overlay.root.after(0, lambda: overlay.update_task_status("plan", "failed"))
            finally:
                pythoncom.CoUninitialize()

        threading.Thread(target=process_planning, daemon=True).start()

    def execute_action_chain(actions, user_text):
        pythoncom.CoInitialize()
        try:
            last_result_path = None
            for i, action_item in enumerate(actions):
                action = action_item.get("action")
                params = action_item.get("params", {})
                explanation = action_item.get("explanation", "Working...")
                
                task_id = f"task_{i}"
                overlay.root.after(0, lambda d=explanation: overlay.add_task_step(task_id, d))
                overlay.root.after(0, lambda: overlay.update_task_status(task_id, "in-progress"))
                
                try:
                    if action == "find_file":
                        # Use description from AI or fallback to user query
                        search_desc = params.get("description") or user_text
                        task = FindFileTask()
                        results, msg = task.run(search_desc)

                        if results:
                            last_result_path = results[0]
                            if i == len(actions) - 1:
                                overlay.root.after(0, lambda r=results: overlay.display_results(r))
                        else:
                            raise Exception(f"Could not find '{search_desc}'")
                            
                    elif action == "organise_folder":
                        path = params.get("path") or last_result_path
                        if not path: raise Exception("No path provided.")
                        task = OrganiseFolderTask()
                        task.run(path)
                        
                    elif action == "open_path":
                        path = params.get("path") or last_result_path
                        if not path: raise Exception("No path provided.")
                        on_select(path)

                    elif action == "copy_path":
                        path = params.get("path") or last_result_path
                        if not path: raise Exception("No path provided.")
                        overlay.root.clipboard_clear()
                        overlay.root.clipboard_append(path)
                        overlay.root.after(0, lambda: overlay.display_message(f"Copied to clipboard: {path}"))
                        
                    elif action == "chat":
                        message = params.get("message", "...")
                        overlay.root.after(0, lambda m=message: overlay.display_message(m))

                    overlay.root.after(0, lambda: overlay.update_task_status(task_id, "completed"))
                    
                except Exception as e:
                    print(f"Action failed: {e}")
                    overlay.root.after(0, lambda: overlay.update_task_status(task_id, "failed"))
                    break

            # Auto-hide logic
            last_action_type = actions[-1].get("action") if actions else None
            if last_action_type in ["organise_folder", "change_cursor", "open_path"]:
                time.sleep(1.5)
                overlay.root.after(0, overlay.hide)
            else:
                overlay.root.after(0, lambda: overlay.entry.config(state='normal'))
        finally:
            pythoncom.CoUninitialize()

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
    
    overlay = OverlayWindow(on_submit=on_submit, on_select=on_select, on_execute=on_execute)
    
    print("CursorOS is running. Press Ctrl+Shift+Space to activate.")
    overlay.run()

if __name__ == "__main__":
    main()
