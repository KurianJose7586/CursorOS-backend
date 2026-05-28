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
        print(f"DEBUG: Initializing Intent Parser 2.0 + Tier 1 Expansion for: '{query}'")
        
        # 1. Intent Parser Layer + Query Expansion
        # We ask for intent and synonyms in one fast call
        system_prompt = """Extract search parameters for a desktop retrieval system.
        Return a JSON object with:
        - keywords: [str] (nouns or identifying tokens)
        - synonyms: [str] (conceptual synonyms, e.g. "datesheet" -> ["timetable", "schedule", "exam"])
        - extensions: [str]
        - temporal_hint: str|null (e.g. "this week", "last month", "2023")
        - semantic_intent: str
        - weights: {
        "recency": float (0.0 to 1.0, higher if user mentions time or "recent"),
        "proximity": float (0.0 to 1.0, higher if user mentions "here" or "this folder"),
        "name_match": float (0.0 to 1.0, base priority for filename similarity)
        }
        - confidence: float
        """
        try:
            intent = llm_service.call(system_prompt, query)
            print(f"DEBUG: Parsed Intent: {json.dumps(intent, indent=2)}")

            base_keywords = intent.get("keywords", [])
            synonyms = intent.get("synonyms", [])
            
            # Refined noise filter
            ignore_words = {'file', 'folder', 'directory', 'find', 'search', 'my', 'the', 'look', 'worked', 'on', 'about', 'get'}
            base_keywords = [kw for kw in base_keywords if kw.lower() not in ignore_words]
            
            # Expanded search set
            all_search_terms = list(set(base_keywords + synonyms))
            
            if not all_search_terms:
                # Fallback: if user just said a word, use it as a keyword
                all_search_terms = [query.split()[-1]]

            print(f"DEBUG: Expanded Search Terms: {all_search_terms}")

            # 2. Parallel Retrieval (Updated to use all_search_terms)
            results_map = {}

            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = {
                    executor.submit(self._retrieve_windows_index, all_search_terms, intent.get("extensions")): "index",
                    executor.submit(self._retrieve_active_context, all_search_terms): "context",
                    executor.submit(self._retrieve_recent_items, all_search_terms): "recent"
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
            ranked_results = self._rank_results(results_map, all_search_terms, intent)
            
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
            
            # If we have keywords, use them in WHERE. If not, rely on extensions/recency
            where_parts = []
            if keywords:
                kw_stmt = " AND ".join([f"System.ItemName LIKE '%{kw}%'" for kw in keywords])
                where_parts.append(f"({kw_stmt})")
            
            if extensions:
                ext_stmt = " OR ".join([f"System.FileExtension = '{e}'" for e in extensions])
                where_parts.append(f"({ext_stmt})")
                
            if not where_parts:
                return []
                
            sql = f"SELECT TOP 50 System.ItemPathDisplay FROM SystemIndex WHERE SCOPE='file:{user_root}' AND " + " AND ".join(where_parts)
            sql += " ORDER BY System.DateModified DESC"
            
            print(f"DEBUG: Index Query: {sql}")
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
        # If no keywords, just return recent items in context roots
        paths = []
        context_roots = [os.path.expanduser("~\\Desktop"), os.getcwd(), os.path.dirname(os.getcwd())]
        
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
                    if depth > 1:
                        dirs[:] = []
                        continue
                    dirs[:] = [d for d in dirs if d not in self.blacklist]
                    
                    for item in files + dirs:
                        if not keywords: # Match everything in active context if no keywords
                            paths.append(os.path.join(root, item))
                        elif any(kw.lower() in item.lower() for kw in keywords):
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
        
        # Extended blacklist for the ranking phase
        RANK_BLACKLIST = {'venv', '.venv', 'env', 'site-packages', 'node_modules', 'AppData', '__pycache__', '.git'}
        
        # Provenance Signals Setup
        username = os.getlogin().lower()
        now = datetime.now()
        
        # Extract weights with defaults
        weights = intent.get("weights", {})
        w_recency = weights.get("recency", 0.5)
        w_proximity = weights.get("proximity", 0.4)
        w_name = weights.get("name_match", 1.0)
        
        # Get active paths from context
        active_paths = []
        try:
            from backend.core.os_context import get_open_explorer_windows
            active_paths = [w.get("path") for w in get_open_explorer_windows() if w.get("path")]
        except: pass

        for path, meta in results_map.items():
            name = os.path.basename(path).lower()
            path_lower = path.lower()
            score = 0.0
            trace = {}

            # 0. CRITICAL: Penalty for "Garbage" paths
            if any(f"\\{b}\\" in path_lower or f"/{b}/" in path_lower for b in RANK_BLACKLIST):
                score -= 5.0 
            
            # 1. Filename Similarity (Weighted by w_name)
            name_score = 0.0
            if any(kw.lower() == name or kw.lower() == os.path.splitext(name)[0] for kw in keywords):
                name_score += 2.0 # Direct match
            elif any(name.startswith(kw.lower()) for kw in keywords):
                name_score += 1.0 # Prefix match
            
            match_count = sum(1 for kw in keywords if kw.lower() in name)
            name_score += (match_count / max(1, len(keywords))) * 0.5
            
            total_name_score = name_score * w_name
            score += total_name_score
            trace["name_score"] = round(total_name_score, 2)

            # 2. Personalization & Context Signals
            p_score = 0.0
            
            # Ownership: User's name in path
            if username in path_lower:
                p_score += 0.40
            
            # Recency: Temporal decay weighted by w_recency
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(path))
                days_old = (now - mtime).days
                
                # Boost if it matches temporal hint (e.g. "this week")
                hint = (intent.get("temporal_hint") or "").lower()
                recency_boost = 1.0
                if "week" in hint and days_old <= 7: recency_boost = 2.0
                elif "month" in hint and days_old <= 30: recency_boost = 1.5
                elif "year" in hint and days_old <= 365: recency_boost = 1.2
                
                # Exponential decay: more aggressive than linear
                decay = 0.5 ** (days_old / 30) # Half-life of 30 days
                p_score += (decay * w_recency * recency_boost)
            except: pass
            
            # Proximity: Weighted by w_proximity
            for ap in active_paths:
                if path_lower.startswith(ap.lower()):
                    p_score += (0.5 * w_proximity)
                    break
            
            score += p_score
            trace["p_score"] = round(p_score, 2)

            # 3. Extension Match
            if intent.get("extensions"):
                if any(path_lower.endswith(e.lower()) for e in intent["extensions"]):
                    score += 0.5
            
            scored.append({
                "path": path, 
                "score": score, 
                "trace": trace
            })
        
        scored.sort(key=lambda x: x["score"], reverse=True)
        
        if scored:
            top = scored[0]
            print(f"DEBUG: Top Match: {top['path']} (Score: {top['score']:.2f})")
            print(f"DEBUG: Trace: {json.dumps(top['trace'])}")
            
        return [x["path"] for x in scored if x["score"] > -1.0]

    def run(self, query: str):
        results = self.search_programmatic(query)
        if results:
            return results, f"Found {len(results)} matching items."
        return [], "No matching items found."
