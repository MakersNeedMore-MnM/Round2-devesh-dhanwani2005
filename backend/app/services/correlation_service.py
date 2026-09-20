"""Correlate related events into a single incident within a time window."""

from collections import defaultdict
from datetime import timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

from app.config import get_settings
from app.utils.time import parse_dt


def _cluster_key(log: Dict[str, Any]) -> Tuple[str, str]:
    user = (log.get("user_name") or "").lower()
    asset = log.get("asset_id") or ""
    ip = log.get("source_ip") or ""
    if user:
        return ("user", user)
    if asset:
        return ("asset", asset)
    if ip:
        return ("ip", ip)
    return ("orphan", log.get("id") or "unknown")


class CorrelationService:
    def window_minutes(self) -> int:
        return get_settings().correlation_window_minutes

    def correlate(self, logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not logs:
            return []
        window = timedelta(minutes=self.window_minutes())
        grouped: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
        for log in logs:
            grouped[_cluster_key(log)].append(log)

        clusters: List[Dict[str, Any]] = []
        for key, items in grouped.items():
            ordered = sorted(items, key=lambda row: parse_dt(row["timestamp"]))
            current: List[Dict[str, Any]] = []
            for log in ordered:
                if not current:
                    current = [log]
                    continue
                if parse_dt(log["timestamp"]) - parse_dt(current[-1]["timestamp"]) <= window:
                    current.append(log)
                else:
                    clusters.append(self._summarize(key, current))
                    current = [log]
            if current:
                clusters.append(self._summarize(key, current))
        return [cluster for cluster in clusters if self._is_incident_worthy(cluster)]

    def _is_incident_worthy(self, cluster: Dict[str, Any]) -> bool:
        types: Set[str] = set(cluster.get("event_types") or [])
        if "failed_login" in types and cluster.get("failed_login_count", 0) >= 5:
            return True
        suspicious = types.intersection(
            {
                "unusual_location",
                "privilege_escalation",
                "large_outbound_transfer",
                "successful_login",
            }
        )
        return len(suspicious) >= 2 or ("failed_login" in types and "successful_login" in types)

    def _summarize(self, key: Tuple[str, str], logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        types = [log.get("event_type") for log in logs]
        failed = sum(1 for item in types if item == "failed_login")
        users = sorted({log.get("user_name") for log in logs if log.get("user_name")})
        assets = sorted({log.get("asset_id") for log in logs if log.get("asset_id")})
        ips = sorted({log.get("source_ip") for log in logs if log.get("source_ip")})
        title = "Possible Account Compromise" if self._looks_like_compromise(types, failed) else "Correlated suspicious activity"
        chain = self._attack_chain(types)
        return {
            "cluster_key": f"{key[0]}:{key[1]}",
            "title": title,
            "description": chain,
            "logs": logs,
            "log_ids": [log["id"] for log in logs if log.get("id")],
            "event_types": sorted(set(t for t in types if t)),
            "failed_login_count": failed,
            "affected_user": users[0] if users else None,
            "affected_asset": assets[0] if assets else None,
            "source_ips": ips,
            "started_at": logs[0]["timestamp"],
            "ended_at": logs[-1]["timestamp"],
        }

    def _looks_like_compromise(self, types: List[Optional[str]], failed: int) -> bool:
        set_types = set(types)
        return failed >= 5 and "successful_login" in set_types

    def _attack_chain(self, types: List[Optional[str]]) -> str:
        labels = {
            "failed_login": "Brute Force",
            "successful_login": "Successful Unauthorized Login",
            "unusual_location": "Unusual Location",
            "privilege_escalation": "Privilege Abuse",
            "large_outbound_transfer": "Possible Data Exfiltration",
        }
        seen = []
        for event_type in types:
            label = labels.get(event_type or "")
            if label and label not in seen:
                seen.append(label)
        if seen:
            return " → ".join(seen)
        return "Multiple related security events in the correlation window"
