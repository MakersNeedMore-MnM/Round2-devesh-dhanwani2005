from typing import Any, Dict

from fastapi import APIRouter, Depends

from app.database import threat_intelligence as intel_repo
from app.schemas.common import ThreatIntelIn
from app.services.auth_service import get_current_user, require_roles

router = APIRouter(prefix="/api/threat-intel", tags=["Threat Intelligence"])


@router.get("")
def list_intel(_: Dict[str, Any] = Depends(get_current_user)):
    return {
        "live_feed": False,
        "notice": "These indicators are sample/internal data, not a live commercial threat feed.",
        "indicators": intel_repo.select(order="created_at", desc=True, limit=200),
    }


@router.post("")
def create_intel(payload: ThreatIntelIn, _: Dict[str, Any] = Depends(require_roles("senior_analyst", "admin"))):
    if payload.indicator_type not in {"ip", "domain", "hash", "email", "url"}:
        from app.utils.errors import AppError
        raise AppError("Unsupported indicator type", status_code=400, code="invalid_indicator")
    inserted = intel_repo.upsert(payload.model_dump(), on_conflict="indicator_type,indicator_value")
    return inserted[0] if inserted else payload
