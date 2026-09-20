"""Create/update incidents from correlated clusters and persist incident_events."""

from typing import Any, Dict, List, Optional

from app.database import assets as assets_repo
from app.database import audit_logs as audit_repo
from app.database import incident_events as events_repo
from app.database import incidents as incidents_repo
from app.database import security_logs as logs_repo
from app.services.correlation_service import CorrelationService
from app.services.detection_service import DetectionService
from app.services.risk_service import RiskService
from app.utils.time import iso, utcnow


def next_incident_number(preferred: Optional[str] = None) -> str:
    if preferred:
        existing = incidents_repo.select(filters={"incident_number": preferred}, limit=1)
        if not existing:
            return preferred
    rows = incidents_repo.select(columns="incident_number", order="created_at", desc=True, limit=50)
    highest = 1000
    for row in rows:
        number = str(row.get("incident_number") or "")
        if number.startswith("CS-"):
            try:
                highest = max(highest, int(number.split("-")[1]))
            except (IndexError, ValueError):
                continue
    return f"CS-{highest + 1}"


class PipelineService:
    def __init__(self) -> None:
        self.detection = DetectionService()
        self.correlation = CorrelationService()
        self.risk = RiskService()

    def process_logs(self, logs: List[Dict[str, Any]], is_demo: bool = False, preferred_number: Optional[str] = None) -> List[Dict[str, Any]]:
        if not logs:
            return []
        clusters = self.correlation.correlate(logs)
        created = []
        for cluster in clusters:
            cluster_logs = cluster["logs"]
            findings = self.detection.evaluate(cluster_logs)["findings"]
            scored = self.risk.score(findings)
            incident = self._upsert_incident(cluster, scored, is_demo=is_demo, preferred_number=preferred_number)
            self._link_events(incident["id"], cluster_logs, findings)
            if cluster.get("affected_asset") and scored["risk_score"] >= 61:
                status = "compromised" if scored["risk_score"] >= 81 else "suspicious"
                assets_repo.update(cluster["affected_asset"], {"status": status, "risk_level": scored["severity"]})
            audit_repo.insert(
                {
                    "incident_id": incident["id"],
                    "action": "incident_correlated",
                    "details": {
                        "cluster_key": cluster.get("cluster_key"),
                        "risk": scored,
                        "findings": [f.get("rule_name") for f in findings],
                    },
                    "is_demo": is_demo,
                }
            )
            created.append({**incident, "risk_factors": scored["factors"], "findings": findings})
            preferred_number = None
        return created

    def process_new_ids(self, log_ids: List[str], is_demo: bool = False) -> List[Dict[str, Any]]:
        if not log_ids:
            return []
        logs = logs_repo.select(in_={"id": log_ids}, order="timestamp", desc=False)
        related = []
        users = {log.get("user_name") for log in logs if log.get("user_name")}
        for user in users:
            related.extend(logs_repo.select(filters={"user_name": user}, order="timestamp", desc=False, limit=500))
        # unique by id
        merged = {row["id"]: row for row in related + logs}
        return self.process_logs(list(merged.values()), is_demo=is_demo)

    def _upsert_incident(
        self,
        cluster: Dict[str, Any],
        scored: Dict[str, Any],
        is_demo: bool,
        preferred_number: Optional[str],
    ) -> Dict[str, Any]:
        open_statuses = ["new", "investigating", "awaiting_approval", "responding"]
        existing = []
        if cluster.get("affected_user"):
            existing = incidents_repo.select(filters={"affected_user": cluster["affected_user"]}, limit=20)
        match = next((row for row in existing if row.get("status") in open_statuses), None)
        payload = {
            "title": cluster["title"],
            "description": cluster["description"],
            "severity": scored["severity"],
            "risk_score": scored["risk_score"],
            "confidence_score": 70,
            "status": "new",
            "detected_at": cluster.get("started_at") or iso(utcnow()),
            "affected_user": cluster.get("affected_user"),
            "affected_asset": cluster.get("affected_asset"),
            "potential_impact": self._impact(cluster),
            "risk_factors": scored["factors"],
            "is_demo": is_demo,
        }
        if match:
            updated = incidents_repo.update(match["id"], payload)
            return updated or match
        payload["incident_number"] = next_incident_number(preferred_number)
        inserted = incidents_repo.insert(payload)
        return inserted[0]

    def _link_events(self, incident_id: str, logs: List[Dict[str, Any]], findings: List[Dict[str, Any]]) -> None:
        high_ids = {log_id for finding in findings for log_id in finding.get("log_ids") or []}
        rows = []
        existing = {
            row["log_id"]
            for row in events_repo.select(filters={"incident_id": incident_id})
        }
        for log in logs:
            if not log.get("id") or log["id"] in existing:
                continue
            relevance = 90 if log["id"] in high_ids else 60
            if log.get("event_type") in {
                "failed_login",
                "successful_login",
                "unusual_location",
                "privilege_escalation",
                "large_outbound_transfer",
            }:
                relevance = max(relevance, 80)
            rows.append(
                {
                    "incident_id": incident_id,
                    "log_id": log["id"],
                    "relevance_score": relevance,
                }
            )
        if rows:
            events_repo.insert(rows)

    def _impact(self, cluster: Dict[str, Any]) -> List[str]:
        types = set(cluster.get("event_types") or [])
        impact = []
        if "successful_login" in types or "failed_login" in types:
            impact.append("Unauthorized access")
        if "privilege_escalation" in types:
            impact.append("Privilege abuse")
        if "large_outbound_transfer" in types:
            impact.append("Possible data exfiltration")
        if "unusual_location" in types:
            impact.append("Session from unexpected location")
        return impact or ["Potential account misuse"]
