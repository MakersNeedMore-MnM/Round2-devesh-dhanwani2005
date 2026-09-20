"""Demo Attack and Reset Demo workflows."""

from typing import Any, Dict

from app.data import load_demo_rows
from app.database import assets as assets_repo
from app.database import audit_logs as audit_repo
from app.database import incident_events as events_repo
from app.database import incidents as incidents_repo
from app.database import investigations as investigations_repo
from app.database import recommendations as recs_repo
from app.database import response_actions as actions_repo
from app.database import security_logs as logs_repo
from app.services.ai_service import AIService
from app.services.ingestion_service import IngestionService
from app.services.pipeline_service import PipelineService
from app.services.response_service import ResponseService
from app.utils.errors import AppError

DEMO_INCIDENT = "CS-1042"
DEMO_ASSET = "aaaaaaaa-0001-4000-8000-000000000001"


class DemoService:
    def __init__(self) -> None:
        self.ingestion = IngestionService()
        self.pipeline = PipelineService()
        self.ai = AIService()
        self.response = ResponseService()

    def load_attack(self, analyst: Dict[str, Any] | None = None) -> Dict[str, Any]:
        self.reset()
        rows = load_demo_rows()
        ingested = self.ingestion.ingest_rows(rows, is_demo=True)
        logs = ingested.get("inserted") or []
        if not logs:
            # duplicates from a partial reset; fetch demo logs
            logs = logs_repo.select(filters={"is_demo": True}, order="timestamp", desc=False)
        incidents = self.pipeline.process_logs(logs, is_demo=True, preferred_number=DEMO_INCIDENT)
        if not incidents:
            raise AppError("Demo correlation did not produce an incident", status_code=500, code="demo_failed")
        incident = incidents[0]
        if incident.get("incident_number") != DEMO_INCIDENT:
            incidents_repo.update(incident["id"], {"incident_number": DEMO_INCIDENT, "is_demo": True, "title": "Possible Account Compromise"})
            incident = incidents_repo.get(incident["id"]) or incident
        investigation = self.ai.investigate(incident, is_demo=True)
        incidents_repo.update(
            incident["id"],
            {
                "ai_summary": investigation.get("ai_assessment", {}).get("summary"),
                "confidence_score": investigation.get("confidence_score") or 92,
                "potential_impact": investigation.get("potential_impact")
                or ["Unauthorized access", "Privilege abuse", "Possible data exfiltration"],
                "status": "investigating",
                "title": "Possible Account Compromise",
            },
        )
        incident = incidents_repo.get(incident["id"]) or incident
        recs = self.response.ensure_recommendations(incident)
        incident = incidents_repo.get(incident["id"]) or incident
        audit_repo.insert(
            {
                "user_id": (analyst or {}).get("id"),
                "incident_id": incident["id"],
                "action": "demo_attack_loaded",
                "details": {
                    "inserted_logs": ingested.get("inserted_count"),
                    "incident_number": DEMO_INCIDENT,
                },
                "is_demo": True,
            }
        )
        return {
            "incident": incident,
            "logs_inserted": ingested.get("inserted_count"),
            "investigation": investigation,
            "recommendations": recs,
            "pipeline": "observe → detect → investigate → reason → plan",
        }

    def reset(self) -> Dict[str, int]:
        demo_incidents = incidents_repo.select(filters={"is_demo": True})
        numbered = incidents_repo.select(filters={"incident_number": DEMO_INCIDENT})
        ids = {row["id"] for row in demo_incidents + numbered}
        for incident_id in ids:
            events_repo.delete({"incident_id": incident_id})
            investigations_repo.delete({"incident_id": incident_id})
            recs_repo.delete({"incident_id": incident_id})
            actions_repo.delete({"incident_id": incident_id})
            audit_repo.delete({"incident_id": incident_id})
            incidents_repo.delete({"id": incident_id})
        logs_repo.delete({"is_demo": True})
        assets_repo.update(DEMO_ASSET, {"status": "healthy", "risk_level": "low"})
        return {"cleared_incidents": len(ids)}
