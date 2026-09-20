from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query

from app.database import incident_events as events_repo
from app.database import incidents as incidents_repo
from app.database import investigations as investigations_repo
from app.database import recommendations as recs_repo
from app.database import security_logs as logs_repo
from app.schemas.common import IncidentIn, IncidentPatch
from app.services.ai_service import AIService
from app.services.auth_service import get_current_user
from app.services.pipeline_service import next_incident_number
from app.services.response_service import ResponseService
from app.utils.errors import AppError, NOT_FOUND
from app.utils.lookups import get_incident_or_404
from app.utils.time import iso, utcnow

router = APIRouter(prefix="/api/incidents", tags=["Incidents"])
ai = AIService()
response = ResponseService()


@router.get("")
def list_incidents(
    search: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    sort: str = Query("detected_at"),
    _: Dict[str, Any] = Depends(get_current_user),
):
    filters = {}
    if severity:
        filters["severity"] = severity
    if status:
        filters["status"] = status
    rows = incidents_repo.select(filters=filters or None, order=sort if sort in {"detected_at", "risk_score", "created_at"} else "detected_at", desc=True, limit=300)
    if search:
        needle = search.lower()
        rows = [
            row
            for row in rows
            if needle in " ".join(str(row.get(key) or "") for key in ("incident_number", "title", "affected_user", "status", "severity")).lower()
        ]
    return rows


@router.post("")
def create_incident(payload: IncidentIn, user: Dict[str, Any] = Depends(get_current_user)):
    row = payload.model_dump()
    row["incident_number"] = next_incident_number()
    row["detected_at"] = iso(utcnow())
    inserted = incidents_repo.insert(row)
    return inserted[0]


@router.get("/{incident_id}")
def get_incident(incident_id: str, _: Dict[str, Any] = Depends(get_current_user)):
    incident = get_incident_or_404(incident_id)
    links = events_repo.select(filters={"incident_id": incident["id"]}, order="created_at", desc=False)
    logs = []
    if links:
        ids = [row["log_id"] for row in links]
        logs = logs_repo.select(in_={"id": ids}, order="timestamp", desc=False)
    recs = recs_repo.select(filters={"incident_id": incident["id"]}, order="created_at", desc=False)
    investigations = investigations_repo.select(filters={"incident_id": incident["id"]}, order="created_at", desc=True, limit=5)
    return {
        **incident,
        "events": logs,
        "incident_events": links,
        "recommendations": recs,
        "investigation": investigations[0] if investigations else None,
    }


@router.patch("/{incident_id}")
def patch_incident(incident_id: str, payload: IncidentPatch, _: Dict[str, Any] = Depends(get_current_user)):
    incident = get_incident_or_404(incident_id)
    data = {key: value for key, value in payload.model_dump().items() if value is not None}
    if data.get("status") == "resolved":
        data["resolved_at"] = iso(utcnow())
    return incidents_repo.update(incident["id"], data)


@router.post("/{incident_id}/investigate")
def investigate(incident_id: str, user: Dict[str, Any] = Depends(get_current_user)):
    incident = get_incident_or_404(incident_id)
    result = ai.investigate(incident, is_demo=incident.get("is_demo", False))
    assessment = result.get("ai_assessment") or {}
    incidents_repo.update(
        incident["id"],
        {
            "ai_summary": assessment.get("summary"),
            "confidence_score": assessment.get("confidence_score") or incident.get("confidence_score"),
            "potential_impact": assessment.get("potential_impact") or incident.get("potential_impact"),
            "status": "investigating" if incident.get("status") == "new" else incident.get("status"),
        },
    )
    response.ensure_recommendations(incidents_repo.get(incident["id"]) or incident, extra=assessment.get("recommendations"))
    return result


@router.get("/{incident_id}/investigation")
def get_investigation(incident_id: str, _: Dict[str, Any] = Depends(get_current_user)):
    incident = get_incident_or_404(incident_id)
    rows = investigations_repo.select(filters={"incident_id": incident["id"]}, order="created_at", desc=True, limit=1)
    if not rows:
        raise AppError("No investigation yet", status_code=NOT_FOUND, code="not_found")
    return rows[0]


@router.get("/{incident_id}/evidence")
def get_evidence(incident_id: str, _: Dict[str, Any] = Depends(get_current_user)):
    incident = get_incident_or_404(incident_id)
    return AIService().gather_evidence(incident)


@router.get("/{incident_id}/recommendations")
def get_recommendations(incident_id: str, _: Dict[str, Any] = Depends(get_current_user)):
    incident = get_incident_or_404(incident_id)
    rows = recs_repo.select(filters={"incident_id": incident["id"]}, order="created_at", desc=False)
    if not rows:
        rows = response.ensure_recommendations(incident)
    return rows
