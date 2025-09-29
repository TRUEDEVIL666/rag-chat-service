# utils_kb.py
from datetime import datetime

PERM_MAP = {
    "only_me": "private",
    "all_team_members": "public",
    "partial_members": "partial",
}

INDEX_MAP = {
    "high_quality": "recursive",
    "economy": "sentence",   
}

def to_epoch(ts) -> int:
    if not ts: return 0
    if isinstance(ts, str):
        try:
            return int(datetime.fromisoformat(ts.replace("Z","+00:00")).timestamp())
        except Exception:
            return 0
    if isinstance(ts, datetime):
        return int(ts.timestamp())
    return 0

def api_to_db_retrieval(api_rm: dict) -> dict:
    if not api_rm: return {}
    rm = dict(api_rm)
    mode = rm.get("reranking_mode") or {}
    if "reranking_provider_name" in mode or "reranking_model_name" in mode:
        rm["reranking_mode"] = {
            "provider": mode.get("reranking_provider_name"),
            "model": mode.get("reranking_model_name"),
        }
    return rm

def db_to_api_retrieval(db_rm: dict) -> dict:
    if not db_rm: return {}
    rm = dict(db_rm)
    mode = rm.get("reranking_mode") or {}
    if "provider" in mode or "model" in mode:
        rm["reranking_mode"] = {
            "reranking_provider_name": mode.get("provider"),
            "reranking_model_name": mode.get("model"),
        }
    return rm
