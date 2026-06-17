import os
import shutil
import json
from backend.core.os_context import get_directory_contents
from backend.core.llm import llm_service

class OrganiseFolderTask:
    def __init__(self):
        self.blacklist = {'.git', 'venv', '.venv', 'node_modules', '__pycache__', '.pytest_cache'}

    def propose(self, path: str):
        """Returns a list of proposed moves: [{'file': str, 'target': str}]"""
        print(f"Generating organization proposal for: {path}")
        contents, truncated = get_directory_contents(path)
        
        # Smart filtering and Token Optimization
        # Only send filenames of actual files (not folders) and limit to 100 items
        file_names = [item['name'] for item in contents 
                     if item['name'] not in self.blacklist and item['type'] == 'file']
        
        if not file_names:
            return [], "No files found to organize (ignored system folders or folder is empty)."

        # Limit to 100 files for token safety (e.g. Groq TPM limits)
        if len(file_names) > 100:
            file_names = file_names[:100]
            print(f"DEBUG: Truncating organization proposal to first 100 files.")

        system_prompt = """You are a file organization expert. 
Given a list of filenames, propose a subfolder structure to organize them.
Return a JSON object with a 'subfolders' key, which is a list of objects:
{ "name": "Folder Name", "files": ["file1.txt", "file2.jpg"] }

Guidelines:
1. Group related files by extension or purpose (e.g., 'Images', 'Documents', 'Code').
2. Only include files that are in the provided list.
"""
        user_prompt = f"Files in {path}:\n" + "\n".join(file_names)
        
        try:
            proposal_data = llm_service.call(system_prompt, user_prompt)
            subfolders = proposal_data.get("subfolders", [])
            
            flattened_proposal = []
            for folder in subfolders:
                target = folder.get("name")
                files = folder.get("files", [])
                for f in files:
                    flattened_proposal.append({
                        "file": f,
                        "target": target
                    })
            
            return flattened_proposal, None
        except Exception as e:
            return [], str(e)

    def execute(self, path: str, proposal: list):
        """Performs the moves defined in the proposal."""
        successful_moves = []
        created_folders = []
        action_log = []
        
        try:
            for move in proposal:
                file_name = move.get("file")
                target_folder = move.get("target")
                
                if not file_name or not target_folder: continue
                
                source_path = os.path.join(path, file_name)
                target_dir = os.path.join(path, target_folder)
                
                if not os.path.exists(source_path): continue
                
                if not os.path.exists(target_dir):
                    os.makedirs(target_dir, exist_ok=True)
                    created_folders.append(target_dir)
                
                dest_path = os.path.join(target_dir, file_name)
                if os.path.exists(dest_path): continue
                
                shutil.move(source_path, dest_path)
                successful_moves.append((dest_path, source_path))
                action_log.append({"file": file_name, "to": target_folder})
                
            return action_log, "Organisation complete."
            
        except Exception as e:
            print(f"Execution failed, rolling back: {e}")
            for dest, src in reversed(successful_moves):
                try: shutil.move(dest, src)
                except: pass
            for folder in reversed(created_folders):
                try:
                    if not os.listdir(folder): os.rmdir(folder)
                except: pass
            return [], f"Error during execution: {str(e)}"

    def run(self, path: str):
        """Legacy support: propose and then immediately execute."""
        proposal, err = self.propose(path)
        if err: return [], err
        return self.execute(path, proposal)
