"""Provider-independent AI investigation. Responses are untrusted structured data."""

import json
import re
from typing import Any, Dict, List, Optional

import httpx

from app.config import get_settings
from app.database import assets as assets_repo
from app.database import incident_events as events_repo
from app.database import investigations as investigations_repo
from app.database import security_logs as logs_repo
from app.database import threat_intelligence as intel_repo
from app.utils.time import iso, utcnow

SYSTEM_PROMPT = """You are a defensive SOC investigation assistant.
Analyze ONLY the supplied evidence. Never invent malware, threat actor names, CVEs,
stolen file names, attacker identities, or locations that are not in the evidence.
Clearly separate FACTS/EVIDENCE from ASSESSMENT.
If evidence is insufficient, say so. Use language such as Possible, Evidence suggests, Potential.
Return a single JSON object with keys:
classification, severity, risk_score, confidence_score, summary, reasoning,
evidence (array of strings), attack_pattern, potential_impact (array), recommendations (array of strings).
Do not include shell commands or exploit steps.
"""


class AIService:
    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.ai_api_key
        self.model = settings.ai_model
        self.base_url = settings.ai_base_url.rstrip("/")
        self.provider = settings.ai_provider

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def gather_evidence(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        links = events_repo.select(filters={"incident_id": incident["id"]}, order="relevance_score", desc=True)
        log_ids = [row["log_id"] for row in links]
        logs = logs_repo.select(in_={"id": log_ids}, order="timestamp", desc=False) if log_ids else []
        user_history = []
        if incident.get("affected_user"):
            user_history = logs_repo.select(
                filters={"user_name": incident["affected_user"]},
                order="timestamp",
                desc=True,
                limit=40,
            )
        asset = assets_repo.get(incident["affected_asset"]) if incident.get("affected_asset") else None
        ips = sorted({log.get("source_ip") for log in logs if log.get("source_ip")})
        intel = []
        for ip in ips:
            intel.extend(intel_repo.select(filters={"indicator_value": ip}))
        return {
            "incident": {
                "id": incident.get("id"),
                "incident_number": incident.get("incident_number"),
                "title": incident.get("title"),
                "description": incident.get("description"),
                "severity": incident.get("severity"),
                "risk_score": incident.get("risk_score"),
                "risk_factors": incident.get("risk_factors"),
                "affected_user": incident.get("affected_user"),
                "status": incident.get("status"),
            },
            "timeline": [
                {
                    "id": log.get("id"),
                    "timestamp": log.get("timestamp"),
                    "event_type": log.get("event_type"),
                    "user_name": log.get("user_name"),
                    "source_ip": log.get("source_ip"),
                    "destination_ip": log.get("destination_ip"),
                    "location": log.get("location"),
                    "severity": log.get("severity"),
                    "message": log.get("message"),
                }
                for log in logs
            ],
            "user_history": [
                {
                    "timestamp": log.get("timestamp"),
                    "event_type": log.get("event_type"),
                    "message": log.get("message"),
                    "source_ip": log.get("source_ip"),
                }
                for log in user_history[:20]
            ],
            "asset": asset,
            "threat_intelligence": intel,
            "observe": "Security events ingested and normalized",
            "detect": "Rule engine matched suspicious patterns",
        }

    def investigate(self, incident: Dict[str, Any], is_demo: bool = False) -> Dict[str, Any]:
        evidence_pack = self.gather_evidence(incident)
        if self.available:
            assessment, provider = self._remote_investigate(evidence_pack)
        else:
            assessment, provider = self._fallback_investigate(evidence_pack), "heuristic_fallback"
        assessment = self._sanitize(assessment, evidence_pack)
        row = {
            "incident_id": incident["id"],
            "investigation_status": "completed",
            "ai_assessment": assessment,
            "reasoning_summary": assessment.get("reasoning"),
            "evidence": assessment.get("evidence"),
            "attack_pattern": assessment.get("attack_pattern"),
            "potential_impact": assessment.get("potential_impact"),
            "confidence_score": int(assessment.get("confidence_score") or 0),
            "is_demo": is_demo or incident.get("is_demo", False),
            "completed_at": iso(utcnow()),
        }
        inserted = investigations_repo.insert(row)
        return {**(inserted[0] if inserted else row), "provider": provider, "evidence_pack": evidence_pack}

    def _remote_investigate(self, evidence_pack: Dict[str, Any]) -> tuple[Dict[str, Any], str]:
        payload = {
            "model": self.model,
            "temperature": 0.1,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "workflow": ["observe", "detect", "investigate", "reason", "plan"],
                            "evidence": evidence_pack,
                            "instructions": "Do not request write/execute tools. Read-only analysis only.",
                        },
                        default=str,
                    ),
                },
            ],
        }
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        try:
            with httpx.Client(timeout=45.0) as client:
                response = client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
                if response.status_code >= 400:
                    return self._fallback_investigate(evidence_pack), "heuristic_fallback_ai_error"
                content = response.json()["choices"][0]["message"]["content"]
                parsed = _extract_json(content)
                return parsed, self.provider
        except Exception:
            return self._fallback_investigate(evidence_pack), "heuristic_fallback_ai_unavailable"

    def _fallback_investigate(self, evidence_pack: Dict[str, Any]) -> Dict[str, Any]:
        timeline = evidence_pack.get("timeline") or []
        types = [item.get("event_type") for item in timeline]
        facts = [f"{item.get('timestamp')} {item.get('event_type')}: {item.get('message')}" for item in timeline]
        failed = sum(1 for item in types if item == "failed_login")
        has_success = "successful_login" in types
        has_location = "unusual_location" in types
        has_priv = "privilege_escalation" in types
        has_xfer = "large_outbound_transfer" in types
        chain = []
        if failed:
            chain.append("Brute Force")
        if has_success:
            chain.append("Successful Unauthorized Login")
        if has_location:
            chain.append("Unusual Location")
        if has_priv:
            chain.append("Privilege Abuse")
        if has_xfer:
            chain.append("Possible Data Exfiltration")
        evidence = []
        if failed:
            evidence.append(f"{failed} failed login attempts")
        if has_success:
            evidence.append("successful login")
        if has_location:
            evidence.append("unusual location")
        if has_priv:
            evidence.append("privilege escalation")
        if has_xfer:
            evidence.append("large outbound transfer")
        impact = []
        if has_success or failed:
            impact.append("Unauthorized access")
        if has_priv:
            impact.append("Privilege abuse")
        if has_xfer:
            impact.append("Possible data exfiltration")
        incident = evidence_pack.get("incident") or {}
        confidence = 70
        if failed >= 10 and has_success and has_location and has_priv and has_xfer:
            confidence = 92
        elif len(evidence) >= 3:
            confidence = 80
        summary = (
            "Evidence suggests a possible account compromise based on a correlated sequence of events. "
            "This is an assessment, not proof of a named attacker or malware family."
        )
        if not evidence:
            summary = "Insufficient evidence to classify a compromise. Additional telemetry is required."
            confidence = 25
        reasoning = (
            "FACTS/EVIDENCE: " + ("; ".join(facts[:12]) or "none supplied") + ". "
            "ASSESSMENT: " + ("Possible account compromise following " + " → ".join(chain) if chain else "inconclusive")
            + ". No malware, CVE, or threat-actor identity is asserted because it is not present in the evidence."
        )
        recs = []
        if evidence:
            recs = [
                "Disable potentially compromised account",
                "Revoke active sessions",
                "Force credential reset",
                "Investigate outbound transfer",
                "Review affected assets",
            ]
        return {
            "classification": "Possible Account Compromise" if chain else "Insufficient evidence",
            "severity": incident.get("severity") or "medium",
            "risk_score": incident.get("risk_score") or 0,
            "confidence_score": confidence,
            "summary": summary,
            "reasoning": reasoning,
            "evidence": evidence,
            "attack_pattern": " → ".join(chain) if chain else "Unknown",
            "potential_impact": impact,
            "recommendations": recs,
            "facts_versus_assessment": {
                "facts": facts,
                "assessment": summary,
            },
        }

    def _sanitize(self, assessment: Dict[str, Any], evidence_pack: Dict[str, Any]) -> Dict[str, Any]:
        allowed_keys = {
            "classification",
            "severity",
            "risk_score",
            "confidence_score",
            "summary",
            "reasoning",
            "evidence",
            "attack_pattern",
            "potential_impact",
            "recommendations",
            "facts_versus_assessment",
        }
        clean = {key: assessment.get(key) for key in allowed_keys if key in assessment}
        for field in ("risk_score", "confidence_score"):
            try:
                clean[field] = max(0, min(100, int(clean.get(field) or 0)))
            except (TypeError, ValueError):
                clean[field] = 0
        for field in ("evidence", "potential_impact", "recommendations"):
            value = clean.get(field) or []
            if isinstance(value, str):
                value = [value]
            clean[field] = [str(item) for item in value]
        # Strip obviously fabricated threat-actor/CVE claims if they were not in evidence text
        blob = json.dumps(evidence_pack, default=str).lower()
        text_fields = " ".join(
            [
                str(clean.get("summary") or ""),
                str(clean.get("reasoning") or ""),
                str(clean.get("attack_pattern") or ""),
            ]
        )
        if re.search(r"\bCVE-\d{4}-\d+\b", text_fields, re.I) and "cve-" not in blob:
            clean["reasoning"] = (clean.get("reasoning") or "") + " CVE identifiers were omitted because they were not present in evidence."
            clean["summary"] = re.sub(r"CVE-\d{4}-\d+", "an unspecified vulnerability (not in evidence)", str(clean.get("summary") or ""), flags=re.I)
        return clean


def _extract_json(content: str) -> Dict[str, Any]:
    content = content.strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, re.S)
        if match:
            return json.loads(match.group(0))
        raise
