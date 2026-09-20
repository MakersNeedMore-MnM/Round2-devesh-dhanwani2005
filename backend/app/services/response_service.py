"""Simulated response engine. High-impact actions never run against real systems."""

from typing import Any, Dict, List, Optional

from app.database import assets as assets_repo
from app.database import audit_logs as audit_repo
from app.database import incidents as incidents_repo
from app.database import recommendations as recs_repo
from app.database import response_actions as actions_repo
from app.utils.time import iso, utcnow

HIGH_IMPACT = {
    "disable_account",
    "revoke_sessions",
    "force_password_reset",
    "isolate_asset",
}

DEFAULT_RECOMMENDATIONS = [
    {
        "action_type": "disable_account",
        "description": "Disable potentially compromised account",
        "priority": "critical",
        "requires_approval": True,
    },
    {
        "action_type": "revoke_sessions",
        "description": "Revoke active sessions",
        "priority": "critical",
        "requires_approval": True,
    },
    {
        "action_type": "force_password_reset",
        "description": "Force credential reset",
        "priority": "high",
        "requires_approval": True,
    },
    {
        "action_type": "investigate_outbound_transfer",
        "description": "Investigate outbound transfer",
        "priority": "high",
        "requires_approval": True,
    },
    {
        "action_type": "review_affected_assets",
        "description": "Review affected assets",
        "priority": "medium",
        "requires_approval": False,
    },
]


class ResponseService:
    def ensure_recommendations(self, incident: Dict[str, Any], extra: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        existing = recs_repo.select(filters={"incident_id": incident["id"]}, order="created_at", desc=False)
        if existing:
            return existing
        rows = []
        for item in DEFAULT_RECOMMENDATIONS:
            rows.append(
                {
                    **item,
                    "incident_id": incident["id"],
                    "status": "pending",
                    "is_demo": incident.get("is_demo", False),
                }
            )
        inserted = recs_repo.insert(rows)
        incidents_repo.update(incident["id"], {"status": "awaiting_approval"})
        audit_repo.insert(
            {
                "incident_id": incident["id"],
                "action": "recommendations_created",
                "details": {"count": len(inserted)},
                "is_demo": incident.get("is_demo", False),
            }
        )
        return inserted

    def approve(
        self,
        incident: Dict[str, Any],
        recommendation: Dict[str, Any],
        analyst: Dict[str, Any],
    ) -> Dict[str, Any]:
        if recommendation.get("requires_approval") and analyst.get("role") not in {"analyst", "senior_analyst", "admin"}:
            raise PermissionError("Insufficient role to approve actions")
        recs_repo.update(recommendation["id"], {"status": "approved"})
        before = {"account_status": "ACTIVE", "sessions": "ACTIVE", "asset_status": None}
        if incident.get("affected_asset"):
            asset = assets_repo.get(incident["affected_asset"])
            before["asset_status"] = asset.get("status") if asset else None
        simulated = self._simulate(recommendation["action_type"], incident, before)
        action_rows = actions_repo.insert(
            {
                "incident_id": incident["id"],
                "recommendation_id": recommendation["id"],
                "action_type": recommendation["action_type"],
                "approved": True,
                "approved_by": analyst.get("id"),
                "execution_status": "simulated",
                "execution_result": simulated,
                "executed_at": iso(utcnow()),
                "verified": False,
                "is_demo": incident.get("is_demo", False),
            }
        )
        recs_repo.update(recommendation["id"], {"status": "executed"})
        incidents_repo.update(incident["id"], {"status": "responding"})
        audit_repo.insert(
            {
                "user_id": analyst.get("id"),
                "incident_id": incident["id"],
                "action": "response_approved_simulated",
                "details": {
                    "recommendation_id": recommendation["id"],
                    "action_type": recommendation["action_type"],
                    "result": simulated,
                    "approved_by": analyst.get("email"),
                },
                "is_demo": incident.get("is_demo", False),
            }
        )
        return action_rows[0] if action_rows else simulated

    def reject(
        self,
        incident: Dict[str, Any],
        recommendation: Dict[str, Any],
        analyst: Dict[str, Any],
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        updated = recs_repo.update(recommendation["id"], {"status": "rejected"})
        actions_repo.insert(
            {
                "incident_id": incident["id"],
                "recommendation_id": recommendation["id"],
                "action_type": recommendation["action_type"],
                "approved": False,
                "approved_by": analyst.get("id"),
                "execution_status": "rejected",
                "execution_result": {"reason": reason or "Rejected by analyst"},
                "is_demo": incident.get("is_demo", False),
            }
        )
        remaining = recs_repo.select(filters={"incident_id": incident["id"]})
        if remaining and all(row.get("status") == "rejected" for row in remaining):
            incidents_repo.update(incident["id"], {"status": "rejected"})
        audit_repo.insert(
            {
                "user_id": analyst.get("id"),
                "incident_id": incident["id"],
                "action": "response_rejected",
                "details": {
                    "recommendation_id": recommendation["id"],
                    "action_type": recommendation["action_type"],
                    "reason": reason,
                    "rejected_by": analyst.get("email"),
                },
                "is_demo": incident.get("is_demo", False),
            }
        )
        return updated or recommendation

    def _simulate(self, action_type: str, incident: Dict[str, Any], before: Dict[str, Any]) -> Dict[str, Any]:
        after = dict(before)
        note = "SIMULATED sandbox action. No production identity provider or host was modified."
        if action_type == "disable_account":
            after["account_status"] = "DISABLED"
        elif action_type == "revoke_sessions":
            after["sessions"] = "REVOKED"
        elif action_type == "force_password_reset":
            after["password_reset"] = "REQUIRED"
        elif action_type == "isolate_asset" and incident.get("affected_asset"):
            assets_repo.update(incident["affected_asset"], {"status": "isolated"})
            after["asset_status"] = "isolated"
        elif action_type == "review_affected_assets":
            after["review"] = "RECORDED"
        elif action_type == "investigate_outbound_transfer":
            after["transfer_review"] = "OPENED"
        return {"mode": "simulated", "before": before, "after": after, "note": note}
