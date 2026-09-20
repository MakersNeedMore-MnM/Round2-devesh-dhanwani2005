from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends

from app.config import get_settings
from app.database import client as db_client
from app.database import incidents as incidents_repo
from app.database import security_logs as logs_repo
from app.schemas.common import DashboardStats, HealthOut
from app.services.ai_service import AIService
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats)
def stats(_: Dict[str, Any] = Depends(get_current_user)) -> DashboardStats:
    events = logs_repo.select(order="timestamp", desc=True, limit=2000)
    incidents = incidents_repo.select(order="detected_at", desc=True, limit=500)
    active_statuses = {"new", "investigating", "awaiting_approval", "responding"}
    by_sev = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    over_time: Dict[str, int] = {}
    risk_buckets = {"0-30": 0, "31-60": 0, "61-80": 0, "81-100": 0}
    for incident in incidents:
        sev = incident.get("severity") or "low"
        by_sev[sev] = by_sev.get(sev, 0) + 1
        day = str(incident.get("detected_at") or "")[:10]
        over_time[day] = over_time.get(day, 0) + 1
        score = int(incident.get("risk_score") or 0)
        if score <= 30:
            risk_buckets["0-30"] += 1
        elif score <= 60:
            risk_buckets["31-60"] += 1
        elif score <= 80:
            risk_buckets["61-80"] += 1
        else:
            risk_buckets["81-100"] += 1
    event_types: Dict[str, int] = {}
    for event in events:
        key = event.get("event_type") or "unknown"
        event_types[key] = event_types.get(key, 0) + 1
    settings = get_settings()
    supabase = "ok"
    try:
        db_client.get_supabase()
    except Exception:
        supabase = "unavailable"
    return DashboardStats(
        total_events=len(events),
        active_incidents=sum(1 for row in incidents if row.get("status") in active_statuses),
        critical_incidents=sum(1 for row in incidents if row.get("severity") == "critical"),
        high_risk_incidents=sum(1 for row in incidents if int(row.get("risk_score") or 0) >= 61),
        resolved_incidents=sum(1 for row in incidents if row.get("status") == "resolved"),
        incidents_by_severity=by_sev,
        incidents_over_time=[{"date": key, "count": value} for key, value in sorted(over_time.items())],
        event_types=[{"type": key, "count": value} for key, value in sorted(event_types.items(), key=lambda item: -item[1])[:12]],
        risk_distribution=[{"bucket": key, "count": value} for key, value in risk_buckets.items()],
        recent_incidents=incidents[:8],
        recent_events=events[:12],
        system_status={
            "supabase": supabase,
            "ai": "configured" if AIService().available else "heuristic_fallback",
            "demo_mode": settings.demo_mode,
            "correlation_window_minutes": settings.correlation_window_minutes,
            "response_engine": "simulated",
        },
    )


health_router = APIRouter(tags=["Health"])


@health_router.get("/health", response_model=HealthOut)
def health() -> HealthOut:
    settings = get_settings()
    supabase = "ok" if settings.supabase_configured else "unconfigured"
    if settings.supabase_configured:
        try:
            db_client.get_supabase().table("detection_rules").select("id").limit(1).execute()
        except Exception:
            supabase = "unavailable"
    return HealthOut(
        status="ok" if supabase != "unavailable" else "degraded",
        supabase=supabase,
        ai="configured" if settings.ai_api_key else "heuristic_fallback",
        demo_mode=settings.demo_mode,
        timestamp=datetime.now(timezone.utc),
    )
