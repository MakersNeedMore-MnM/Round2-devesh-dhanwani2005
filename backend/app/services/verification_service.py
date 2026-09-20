"""Verify whether simulated containment appears successful."""

from typing import Any, Dict

from app.database import audit_logs as audit_repo
from app.database import incidents as incidents_repo
from app.database import response_actions as actions_repo
from app.database import security_logs as logs_repo
from app.utils.time import parse_dt


class VerificationService:
    def verify_incident(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        actions = actions_repo.select(filters={"incident_id": incident["id"]}, order="executed_at", desc=True)
        executed = [row for row in actions if row.get("execution_status") == "simulated" and row.get("approved")]
        if not executed:
            result = {
                "status": "pending",
                "verified": False,
                "detail": "No simulated response has been executed yet.",
            }
            return result

        user = incident.get("affected_user")
        latest_exec = None
        for row in executed:
            if row.get("executed_at"):
                latest_exec = parse_dt(row["executed_at"])
                break

        new_success = []
        if user and latest_exec:
            logs = logs_repo.select(filters={"user_name": user, "event_type": "successful_login"}, order="timestamp", desc=False)
            new_success = [
                log
                for log in logs
                if parse_dt(log["timestamp"]) > latest_exec and not log.get("is_demo")
            ]

        disabled = any(row.get("action_type") == "disable_account" for row in executed)
        if disabled and not new_success:
            status = "contained"
            detail = "Containment verified: no new successful logins observed for the affected account after simulated disable."
            verified = True
        elif disabled and new_success:
            status = "failed"
            detail = "Verification failed: a successful login was observed after simulated account disable."
            verified = False
        else:
            status = "contained"
            detail = "Simulated responses executed. No contradictory telemetry observed in the sandbox."
            verified = True

        verification = {"status": status, "verified": verified, "detail": detail, "post_action_logins": len(new_success)}
        for row in executed:
            actions_repo.update(row["id"], {"verified": verified, "verification_result": verification})

        payload: Dict[str, Any] = {"status": "contained" if verified else "responding"}
        if verified:
            payload["status"] = "contained"
        incidents_repo.update(incident["id"], payload)
        audit_repo.insert(
            {
                "incident_id": incident["id"],
                "action": "verification_completed",
                "details": verification,
                "is_demo": incident.get("is_demo", False),
            }
        )
        return verification

    def resolve(self, incident: Dict[str, Any], analyst: Dict[str, Any]) -> Dict[str, Any]:
        from app.utils.time import iso, utcnow

        updated = incidents_repo.update(
            incident["id"],
            {"status": "resolved", "resolved_at": iso(utcnow())},
        )
        audit_repo.insert(
            {
                "user_id": analyst.get("id"),
                "incident_id": incident["id"],
                "action": "incident_resolved",
                "details": {"by": analyst.get("email")},
                "is_demo": incident.get("is_demo", False),
            }
        )
        return updated or incident
