from typing import Any, Dict, List, Optional

from app.database import incidents as incidents_repo
from app.database import recommendations as recs_repo
from app.database import security_logs as logs_repo
from app.utils.errors import AppError, NOT_FOUND


def get_incident_or_404(incident_id: str) -> Dict[str, Any]:
    incident = incidents_repo.get(incident_id)
    if not incident:
        rows = incidents_repo.select(filters={"incident_number": incident_id}, limit=1)
        incident = rows[0] if rows else None
    if not incident:
        raise AppError("Incident not found", status_code=NOT_FOUND, code="not_found")
    return incident


def get_recommendation(incident_id: str, action_id: str) -> Dict[str, Any]:
    rec = recs_repo.get(action_id)
    if rec and rec.get("incident_id") == incident_id:
        return rec
    raise AppError("Recommendation not found", status_code=NOT_FOUND, code="not_found")


def query_logs(
    search: Optional[str] = None,
    severity: Optional[str] = None,
    event_type: Optional[str] = None,
    user_name: Optional[str] = None,
    limit: int = 200,
) -> List[Dict[str, Any]]:
    filters = {}
    if severity:
        filters["severity"] = severity
    if event_type:
        filters["event_type"] = event_type
    if user_name:
        filters["user_name"] = user_name
    rows = logs_repo.select(filters=filters or None, order="timestamp", desc=True, limit=limit)
    if search:
        needle = search.lower()
        rows = [
            row
            for row in rows
            if needle in " ".join(
                str(row.get(key) or "")
                for key in ("user_name", "event_type", "source_ip", "destination_ip", "message", "location")
            ).lower()
        ]
    return rows
