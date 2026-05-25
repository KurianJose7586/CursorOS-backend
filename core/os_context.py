import os
import win32com.client
from datetime import datetime

def get_open_explorer_windows():
    """Returns a list of dicts: { 'title': str, 'path': str }"""
    windows = []
    try:
        shell = win32com.client.Dispatch("Shell.Application")
        for window in shell.Windows():
            # Check if it's an Explorer window (not IE)
            if "explorer.exe" in window.FullName.lower():
                path = window.LocationURL
                # Convert file:///URL to local path
                if path.startswith("file:///"):
                    path = path.replace("file:///", "").replace("/", "\\")
                    # Handle spaces (%20)
                    path = path.replace("%20", " ")
                
                windows.append({
                    "title": window.LocationName,
                    "path": path
                })
    except Exception as e:
        print(f"Error getting explorer windows: {e}")
    
    return windows

def get_directory_contents(path: str):
    """Returns a list of dicts: { 'name': str, 'type': 'file'|'folder', 'extension': str, 'modified': datetime }"""
    items = []
    truncated = False
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"Path does not exist: {path}")
        
    try:
        with os.scandir(path) as it:
            for entry in it:
                if len(items) >= 200:
                    truncated = True
                    break
                
                stats = entry.stat()
                is_file = entry.is_file()
                
                items.append({
                    "name": entry.name,
                    "type": "file" if is_file else "folder",
                    "extension": os.path.splitext(entry.name)[1] if is_file else "",
                    "modified": datetime.fromtimestamp(stats.st_mtime).isoformat()
                })
    except PermissionError:
        print(f"Permission denied: {path}")
        # Return what we have or raise? Strategy says handle gracefully.
    
    return items, truncated
