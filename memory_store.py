import json
import os
from typing import List, Dict, Any

class JsonMessageHistoryStore:
    def __init__(self, path: str):
        self.path = path
        if not os.path.exists(self.path):
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump({}, f)

    def _load_db(self) -> Dict[str, Any]:
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            db = {}
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(db, f)
            return db

    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        db = self._load_db()
        return db.get(session_id, [])

    def set_history(self, session_id: str, history: List[Dict[str, str]]):
        db = self._load_db()
        db[session_id] = history
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(db, f, indent=2, ensure_ascii=False)