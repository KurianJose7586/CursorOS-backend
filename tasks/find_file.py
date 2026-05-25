import os
import json
import win32com.client
import pythoncom
import concurrent.futures
from datetime import datetime, timedelta
from backend.core.llm import llm_service
from backend.core.os_context import get_open_explorer_windows

class FindFileTask:
    def __init__(self):
        self.blacklist = {'node_modules', '.git', '.venv', 'venv', 'env', '__pycache__', 'AppData'}

    def search_programmatic(self, query: str) -> list:
        print(f"DEBUG: Initializing Intent Parser 2.0 for: '{query}'")
        
        # 1. Intent Parser Layer
        system_prompt = """Extract search parameters for a desktop retrieval system.
Return a JSON object with:
- keywords: [str] (filename tokens, avoid generic words)
- extensions: [str] (e.g. [".pdf", ".docx"])
- temporal_hint: str|null ("today", "yesterday", "this_week", "older")
- semantic_intent: str (e.g. "document", "image", "project", "folder")
- confidence: float (0.0 to 1.0)
"""
        try:
            intent = llm_service.call(system_prompt, query)
            print(f"DEBUG: Parsed Intent: {json.dumps(intent, indent=2)}")
            
            keywords = intent.get("keywords", [])
            # Manual cleanup of common noise
            intent_words = {'file', 'folder', 'directory', 'find', 'search', 'my', 'the', 'look'}
            keywords = [kw for kw in keywords if kw.lower() not in intent_words]
            
            if not keywords: return []

            # 2. Parallel Retrieval
            results_map = {} # path -> metadata dict

            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = {
                    executor.submit(self._retrieve_windows_index, keywords, intent.get("extensions")): "index",
                    executor.submit(self._retrieve_active_context, keywords): "context",
                    executor.submit(self._retrieve_recent_items, keywords): "recent"
                }

                for future in concurrent.futures.as_completed(futures):
                    strategy = futures[future]
                    try:
                        strategy_results = future.result()
                        for path in strategy_results:
                            if path not in results_map:
                                results_map[path] = {"strategies": [], "score": 0.0}
                            results_map[path]["strategies"].append(strategy)
                    except Exception as e:
                        print(f"DEBUG: Strategy {strategy} failed: {e}")

            # 3. Ranking Layer
            ranked_results = self._rank_results(results_map, keywords, intent)
            
            print(f"DEBUG: Parallel Search complete. Found {len(ranked_results)} unique items.")
            return ranked_results[:10]

        except Exception as e:
            print(f"DEBUG: Intent Parsing Error: {e}")
            return []

    def _retrieve_windows_index(self, keywords, extensions) -> list:
        paths = []
        pythoncom.CoInitialize()
        try:
            conn = win32com.client.Dispatch("ADODB.Connection")
            rs = win32com.client.Dispatch("ADODB.Recordset")
            conn.Open("Provider=Search.CollatorDSO;Extended Properties='Application=Windows';")
            
            user_root = os.path.expanduser("~").replace("\\", "/")
            where_clauses = [f"System.ItemName LIKE '%{kw}%'" for kw in keywords]
            where_stmt = " AND ".join(where_clauses)
            
            sql = f"SELECT TOP 30 System.ItemPathDisplay FROM SystemIndex WHERE SCOPE='file:{user_root}' AND ({where_stmt})"
            if extensions:
                ext_stmt = " OR ".join([f"System.FileExtension = '{e}'" for e in extensions])
                sql += f" AND ({ext_stmt})"
            
            rs.Open(sql, conn)
            while not rs.EOF:
                path = rs.Fields.Item("System.ItemPathDisplay").Value
                if path: paths.append(path)
                rs.MoveNext()
            rs.Close()
            conn.Close()
        finally:
            pythoncom.CoUninitialize()
        return paths

    def _retrieve_active_context(self, keywords) -> list:
        paths = []
        context_roots = [
            os.path.expanduser("~\\Desktop"),
            os.getcwd(),
            os.path.dirname(os.getcwd())
        ]
        
        # Add open explorer windows
        pythoncom.CoInitialize()
        try:
            windows = get_open_explorer_windows()
            for w in windows:
                if w.get("path"): context_roots.append(w["path"])
        finally:
            pythoncom.CoUninitialize()

        for base in set(context_roots):
            if not os.path.exists(base): continue
            try:
                for root, dirs, files in os.walk(base):
                    depth = root[len(base):].count(os.sep)
                    if depth > 1: # Shallow for speed
                        dirs[:] = []
                        continue
                    dirs[:] = [d for d in dirs if d not in self.blacklist]
                    
                    for item in files + dirs:
                        if any(kw.lower() in item.lower() for kw in keywords):
                            paths.append(os.path.join(root, item))
            except Exception: pass
        return paths

    def _retrieve_recent_items(self, keywords) -> list:
        # Placeholder for real Windows Recent Items API
        # For now, just looks at the root of Downloads as a proxy for "recent stuff"
        paths = []
        downloads = os.path.join(os.path.expanduser("~"), "Downloads")
        if os.path.exists(downloads):
            try:
                with os.scandir(downloads) as it:
                    for entry in it:
                        if any(kw.lower() in entry.name.lower() for kw in keywords):
                            paths.append(entry.path)
            except Exception: pass
        return paths

    def _rank_results(self, results_map: dict, keywords: list, intent: dict) -> list:
        scored = []
        
        for path, meta in results_map.items():
            name = os.path.basename(path)
            score = 0.0
            
            # 1. Filename Similarity (35%)
            match_count = sum(1 for kw in keywords if kw.lower() in name.lower())
            score += (match_count / len(keywords)) * 0.35
            
            # 2. Strategy Weighting
            if "recent" in meta["strategies"]: score += 0.20 # Recency bias
            if "context" in meta["strategies"]: score += 0.15 # Proximity bias
            
            # 3. Extension Match (15%)
            if intent.get("extensions"):
                if any(path.lower().endswith(e.lower()) for e in intent["extensions"]):
                    score += 0.15
            
            # 4. Multi-Strategy Bonus
            if len(meta["strategies"]) > 1:
                score += 0.10 # Confidence boost
                
            scored.append((path, score))
        
        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)
        return [x[0] for x in scored]

    def run(self, query: str):
        results = self.search_programmatic(query)
        if results:
            return results, f"Found {len(results)} matching items."
        return [], "No matching items found."
