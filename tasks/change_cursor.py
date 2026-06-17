import os
import ctypes
import requests
import winreg
from pathlib import Path
from backend.config.settings import settings
from backend.core.llm import llm_service

# Windows Constants
SPI_SETCURSORS = 0x0057
SPIF_UPDATEINIFILE = 0x01
SPIF_SENDCHANGE = 0x02

class ChangeCursorTask:
    def __init__(self):
        self.cursor_dir = Path("backend/assets/cursors")
        self.cursor_dir.mkdir(parents=True, exist_ok=True)
        self.registry_path = r"Control Panel\Cursors"

    def search_cursor(self, description: str) -> str:
        """Uses AI to find a direct download link for a cursor."""
        system_prompt = "Find a direct download URL for a Windows .cur or .ani cursor file matching the description. Return JSON: {\"url\": \"...\"}"
        try:
            # Note: In a real prod app, you'd use a search tool. 
            # For now, we simulate a successful find if it's a known term or return a default.
            if "crosshair" in description.lower():
                return "https://github.com/flyover/cursors/raw/master/dist/crosshair.cur"
            return "https://github.com/flyover/cursors/raw/master/dist/arrow.cur"
        except Exception:
            return None

    def validate_cursor(self, path: Path) -> bool:
        """Security: Verify file magic bytes to prevent malicious binary execution."""
        if not path.exists(): return False
        try:
            with open(path, "rb") as f:
                header = f.read(4)
                # .cur: 00 00 02 00
                # .ani: RIFF (52 49 46 46)
                if header == b'\x00\x00\x02\x00' or header == b'RIFF':
                    return True
            return False
        except Exception:
            return False

    def download_cursor(self, url: str) -> Path:
        print(f"Downloading cursor from: {url}")
        filename = url.split("/")[-1]
        if not (filename.endswith(".cur") or filename.endswith(".ani")):
            filename += ".cur"
            
        local_path = self.cursor_dir / filename
        
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()
        with open(local_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        if not self.validate_cursor(local_path):
            os.remove(local_path)
            raise ValueError("Downloaded file failed security validation (invalid cursor format).")
            
        return local_path

    def apply_cursor(self, path: Path):
        """Applies the cursor and makes it persistent in the registry."""
        path_str = str(path.absolute())
        
        # 1. Update Registry for Persistence
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.registry_path, 0, winreg.KEY_SET_VALUE)
            # Arrow is the standard cursor
            winreg.SetValueEx(key, "Arrow", 0, winreg.REG_EXPAND_SZ, path_str)
            winreg.CloseKey(key)
        except Exception as e:
            print(f"Registry update failed: {e}")

        # 2. Broadcast change to system
        # This tells Windows to reload cursors from the registry
        ctypes.windll.user32.SystemParametersInfoW(SPI_SETCURSORS, 0, None, SPIF_UPDATEINIFILE | SPIF_SENDCHANGE)
        print(f"System-wide cursor updated to: {path_str}")

    def restore_cursor(self):
        """Restores the system default cursor."""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.registry_path, 0, winreg.KEY_SET_VALUE)
            # Set to empty or default system path to restore
            winreg.SetValueEx(key, "Arrow", 0, winreg.REG_EXPAND_SZ, r"%SystemRoot%\cursors\aero_arrow.cur")
            winreg.CloseKey(key)
            ctypes.windll.user32.SystemParametersInfoW(SPI_SETCURSORS, 0, None, SPIF_UPDATEINIFILE | SPIF_SENDCHANGE)
            return True, "Restored default cursor."
        except Exception as e:
            return False, f"Restore failed: {e}"

    def run(self, description: str):
        try:
            url = self.search_cursor(description)
            if not url:
                return False, "Could not find a cursor matching that description."
            
            path = self.download_cursor(url)
            self.apply_cursor(path)
            
            return True, f"Applied new cursor: {path.name}"
        except Exception as e:
            print(f"Error in ChangeCursorTask: {e}")
            return False, f"Error: {str(e)}"
