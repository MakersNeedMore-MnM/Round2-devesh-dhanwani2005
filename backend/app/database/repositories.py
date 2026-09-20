from typing import Any, Dict, List, Optional

from postgrest.exceptions import APIError

from app.database.client import get_supabase


def _data(result) -> Any:
    return result.data


class Repository:
    def __init__(self, table: str):
        self.table = table

    def select(
        self,
        columns: str = "*",
        filters: Optional[Dict[str, Any]] = None,
        order: Optional[str] = None,
        desc: bool = True,
        limit: Optional[int] = None,
        gte: Optional[Dict[str, Any]] = None,
        lte: Optional[Dict[str, Any]] = None,
        in_: Optional[Dict[str, List[Any]]] = None,
        ilike: Optional[Dict[str, str]] = None,
        neq: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        query = get_supabase().table(self.table).select(columns)
        for key, value in (filters or {}).items():
            query = query.eq(key, value)
        for key, value in (gte or {}).items():
            query = query.gte(key, value)
        for key, value in (lte or {}).items():
            query = query.lte(key, value)
        for key, value in (in_ or {}).items():
            query = query.in_(key, value)
        for key, value in (ilike or {}).items():
            query = query.ilike(key, value)
        for key, value in (neq or {}).items():
            query = query.neq(key, value)
        if order:
            query = query.order(order, desc=desc)
        if limit:
            query = query.limit(limit)
        return _data(query.execute()) or []

    def get(self, record_id: str) -> Optional[Dict[str, Any]]:
        rows = self.select(filters={"id": record_id}, limit=1)
        return rows[0] if rows else None

    def insert(self, payload: Dict[str, Any] | List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        result = get_supabase().table(self.table).insert(payload).execute()
        return _data(result) or []

    def update(self, record_id: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        result = get_supabase().table(self.table).update(payload).eq("id", record_id).execute()
        rows = _data(result) or []
        return rows[0] if rows else None

    def delete(self, filters: Dict[str, Any]) -> None:
        query = get_supabase().table(self.table).delete()
        for key, value in filters.items():
            query = query.eq(key, value)
        query.execute()

    def upsert(self, payload: Dict[str, Any], on_conflict: str) -> List[Dict[str, Any]]:
        result = (
            get_supabase()
            .table(self.table)
            .upsert(payload, on_conflict=on_conflict)
            .execute()
        )
        return _data(result) or []


def is_api_error(exc: Exception) -> bool:
    return isinstance(exc, APIError)


profiles = Repository("profiles")
assets = Repository("assets")
security_logs = Repository("security_logs")
incidents = Repository("incidents")
incident_events = Repository("incident_events")
investigations = Repository("investigations")
recommendations = Repository("recommendations")
response_actions = Repository("response_actions")
threat_intelligence = Repository("threat_intelligence")
audit_logs = Repository("audit_logs")
detection_rules = Repository("detection_rules")
app_settings = Repository("app_settings")
