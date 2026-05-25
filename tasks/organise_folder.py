import os
import shutil
import json
from backend.core.os_context import get_directory_contents
from backend.core.llm import llm_service

class OrganiseFolderTask:
    def run(self, path: str):
        print(f"Organising folder: {path}")
        contents, truncated = get_directory_contents(path)
        
        if not contents:
            return [], "Folder is empty."

        system_prompt = """You are a file organization expert. 
Given a list of files and folders, propose a subfolder structure to organize them.
Return a JSON object with a 'subfolders' key, which is a list of objects:
{ "name": "Folder Name", "files": ["file1.txt", "file2.jpg"] }

Only include files that are in the provided list. Do not include folders in the 'files' list.
"""
        user_prompt = f"Contents of {path}:\n{json.dumps(contents, indent=2)}"
        
        try:
            proposal = llm_service.call(system_prompt, user_prompt)
            subfolders = proposal.get("subfolders", [])
            
            action_log = []
            for folder_info in subfolders:
                folder_name = folder_info.get("name")
                files_to_move = folder_info.get("files", [])
                
                if not folder_name or not files_to_move:
                    continue
                    
                target_dir = os.path.join(path, folder_name)
                os.makedirs(target_dir, exist_ok=True)
                action_log.append({"action": "created_folder", "name": folder_name})
                
                for file_name in files_to_move:
                    source_path = os.path.join(path, file_name)
                    if os.path.exists(source_path) and os.path.isfile(source_path):
                        dest_path = os.path.join(target_dir, file_name)
                        shutil.move(source_path, dest_path)
                        action_log.append({
                            "action": "moved_file", 
                            "name": file_name, 
                            "destination": folder_name
                        })
            
            return action_log, "Organisation complete."
            
        except Exception as e:
            print(f"Error in OrganiseFolderTask: {e}")
            return [], f"Error: {str(e)}"
