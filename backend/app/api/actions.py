from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.database import incidents as incidents_repo
from app.database import recommendations as recs_repo
from app.database import response_actions as actions_repo
from app.services.auth_service import get_current_user
from app.services.response_service import ResponseService
from app.services.verification_service import VerificationService
from app.utils.lookups import get_incident_or_404, get_recommendation

router = APIRouter(prefix="/api", tags=["Actions"])
response = ResponseService()
verification = VerificationService()


class RejectBody(BaseModel):
    reason: Optional[str] = None


@router.post("/incidents/{incident_id}/actions/{action_id}/approve")
def approve_action(incident_id: str, action_id: str, user: Dict[str, Any] = Depends(get_current_user)):
    incident = get_incident_or_404(incident_id)
    rec = get_recommendation(incident["id"], action_id)
    action = response.approve(incident, rec, user)
    verify = verification.verify_incident(incidents_repo.get(incident["id"]) or incident)
    return {"action": action, "verification": verify, "incident": incidents_repo.get(incident["id"])}


@router.post("/incidents/{incident_id}/actions/{action_id}/reject")
def reject_action(incident_id: str, action_id: str, body: RejectBody | None = None, user: Dict[str, Any] = Depends(get_current_user)):
    incident = get_incident_or_404(incident_id)
    rec = get_recommendation(incident["id"], action_id)
    updated = response.reject(incident, rec, user, reason=(body.reason if body else None))
    return {"recommendation": updated, "incident": incidents_repo.get(incident["id"])}


@router.post("/incidents/{incident_id}/verify")
def verify(incident_id: str, _: Dict[str, Any] = Depends(get_current_user)):
    incident = get_incident_or_404(incident_id)
    result = verification.verify_incident(incident)
    return {"verification": result, "incident": incidents_repo.get(incident["id"])}


@router.post("/incidents/{incident_id}/resolve")
def resolve(incident_id: str, user: Dict[str, Any] = Depends(get_current_user)):
    incident = get_incident_or_404(incident_id)
    if incident.get("status") != "contained":
        verification.verify_incident(incident)
        incident = incidents_repo.get(incident["id"]) or incident
    if incident.get("status") != "contained":
        from app.utils.errors import AppError
        raise AppError("Incident must be contained before it can be resolved", status_code=400, code="not_contained")
    return verification.resolve(incident, user)


@router.get("/incidents/{incident_id}/actions")
def list_actions(incident_id: str, _: Dict[str, Any] = Depends(get_current_user)):
    incident = get_incident_or_404(incident_id)
    return {
        "recommendations": recs_repo.select(filters={"incident_id": incident["id"]}, order="created_at", desc=False),
        "actions": actions_repo.select(filters={"incident_id": incident["id"]}, order="executed_at", desc=True),
    }
