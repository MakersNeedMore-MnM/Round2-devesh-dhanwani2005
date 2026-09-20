"""Rule-based detection. Rules are loaded from detection_rules, not routes."""

from collections import defaultdict
from datetime import timedelta
from typing import Any, Dict, List

from app.config import get_settings
from app.database import detection_rules as rules_repo
from app.database import threat_intelligence as intel_repo
from app.utils.time import parse_dt


class DetectionService:
    def load_rules(self) -> List[Dict[str, Any]]:
        return [row for row in rules_repo.select(order="rule_name", desc=False) if row.get("enabled")]

    def evaluate(self, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        rules = {row["rule_name"]: row for row in self.load_rules()}
        settings = get_settings()
        window = timedelta(minutes=settings.correlation_window_minutes)
        intel_ips = {
            row["indicator_value"]
            for row in intel_repo.select(filters={"indicator_type": "ip"})
            if str(row.get("reputation", "")).lower() in {"malicious", "suspicious"}
        }

        findings: List[Dict[str, Any]] = []

        by_user: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        by_asset: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for log in logs:
            if log.get("user_name"):
                by_user[log["user_name"]].append(log)
            if log.get("asset_id"):
                by_asset[log["asset_id"]].append(log)

        def add(rule_name: str, matched_logs: List[Dict[str, Any]], detail: str) -> None:
            rule = rules.get(rule_name)
            if not rule:
                return
            findings.append(
                {
                    "rule_name": rule_name,
                    "description": rule.get("description"),
                    "severity": rule.get("severity"),
                    "weight": int(rule.get("weight") or 0),
                    "detail": detail,
                    "log_ids": [item["id"] for item in matched_logs if item.get("id")],
                    "event_types": sorted({item.get("event_type") for item in matched_logs}),
                }
            )

        for user, items in by_user.items():
            items = sorted(items, key=lambda row: row["timestamp"])
            for index, event in enumerate(items):
                start = parse_dt(event["timestamp"])
                window_events = [
                    other
                    for other in items
                    if start <= parse_dt(other["timestamp"]) <= start + window
                ]
                failed = [e for e in window_events if e.get("event_type") == "failed_login"]
                rule = rules.get("failed_login_burst")
                if rule and len(failed) >= int(rule.get("threshold") or 5):
                    add("failed_login_burst", failed, f"{len(failed)} failed logins for {user}")

                if event.get("event_type") == "successful_login":
                    prior_failed = [
                        e
                        for e in items[:index]
                        if e.get("event_type") == "failed_login"
                        and parse_dt(event["timestamp"]) - parse_dt(e["timestamp"]) <= window
                    ]
                    if prior_failed and "success_after_failures" in rules:
                        add(
                            "success_after_failures",
                            prior_failed + [event],
                            f"Successful login for {user} after {len(prior_failed)} failures",
                        )

            unusual = [e for e in items if e.get("event_type") == "unusual_location"]
            if unusual:
                add("unusual_location", unusual, f"Unusual location activity for {user}")
            priv = [e for e in items if e.get("event_type") == "privilege_escalation"]
            if priv:
                add("privilege_escalation", priv, f"Privilege escalation for {user}")
            xfer = [e for e in items if e.get("event_type") in {"large_outbound_transfer", "data_exfiltration"}]
            if xfer:
                add("large_outbound_transfer", xfer, f"Large outbound transfer associated with {user}")

            suspicious_types = {
                e.get("event_type")
                for e in items
                if e.get("event_type")
                in {
                    "failed_login",
                    "successful_login",
                    "unusual_location",
                    "privilege_escalation",
                    "large_outbound_transfer",
                }
            }
            multi_rule = rules.get("multi_user_suspicious")
            if multi_rule and len(suspicious_types) >= int(multi_rule.get("threshold") or 3):
                add("multi_user_suspicious", items, f"{len(suspicious_types)} suspicious event types for {user}")

        for asset_id, items in by_asset.items():
            types = {e.get("event_type") for e in items}
            multi_rule = rules.get("multi_asset_suspicious")
            if multi_rule and len(types) >= int(multi_rule.get("threshold") or 3):
                add("multi_asset_suspicious", items, f"Multiple suspicious events on asset {asset_id}")

        for log in logs:
            ip = log.get("source_ip") or log.get("destination_ip")
            if ip and ip in intel_ips:
                add("suspicious_ip", [log], f"Activity involving indicator {ip}")

        # Deduplicate findings by rule+detail
        unique = {}
        for finding in findings:
            unique[(finding["rule_name"], finding["detail"])] = finding
        return {"findings": list(unique.values()), "rules_evaluated": list(rules.keys())}
