"""Normalize heterogeneous security logs into security_logs rows."""

from datetime import timezone
from typing import Any, Dict, List, Optional, Tuple

from app.database import assets as assets_repo
from app.utils.time import fingerprint, iso, parse_dt, utcnow

FIELD_ALIASES = {
    "timestamp": ["timestamp", "time", "event_time", "@timestamp", "datetime"],
    "user_name": ["user_name", "user", "username", "account", "actor"],
    "event_type": ["event_type", "event", "action", "type", "category"],
    "source_ip": ["source_ip", "src_ip", "src", "ip", "client_ip"],
    "destination_ip": ["destination_ip", "dest_ip", "dst_ip", "dst", "target_ip"],
    "asset": ["asset", "asset_name", "host", "hostname", "device"],
    "asset_id": ["asset_id"],
    "location": ["location", "geo", "city", "country"],
    "severity": ["severity", "level", "priority"],
    "message": ["message", "msg", "description", "summary"],
}

SEVERITY_MAP = {
    "info": "low",
    "informational": "low",
    "low": "low",
    "warn": "medium",
    "warning": "medium",
    "medium": "medium",
    "high": "high",
    "error": "high",
    "critical": "critical",
    "crit": "critical",
    "fatal": "critical",
}


def _pick(row: Dict[str, Any], keys: List[str]) -> Any:
    lowered = {str(k).lower(): v for k, v in row.items()}
    for key in keys:
        if key.lower() in lowered and lowered[key.lower()] not in (None, ""):
            return lowered[key.lower()]
    return None


def _severity(value: Any) -> str:
    text = str(value or "low").strip().lower()
    return SEVERITY_MAP.get(text, "low" if text not in {"low", "medium", "high", "critical"} else text)


class NormalizationService:
    def __init__(self) -> None:
        self._asset_cache: Dict[str, str] = {}

    def _resolve_asset_id(self, asset_id: Optional[str], asset_name: Optional[str]) -> Optional[str]:
        if asset_id:
            return str(asset_id)
        if not asset_name:
            return None
        key = asset_name.lower()
        if key in self._asset_cache:
            return self._asset_cache[key]
        rows = assets_repo.select(ilike={"asset_name": asset_name}, limit=5)
        if not rows:
            rows = assets_repo.select(ilike={"hostname": f"%{asset_name}%"}, limit=5)
        if rows:
            self._asset_cache[key] = rows[0]["id"]
            return rows[0]["id"]
        return None

    def normalize_row(self, row: Dict[str, Any], is_demo: bool = False) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        if not isinstance(row, dict):
            return None, "Each log entry must be an object"
        timestamp_raw = _pick(row, FIELD_ALIASES["timestamp"]) or iso(utcnow())
        try:
            ts = parse_dt(timestamp_raw).astimezone(timezone.utc)
        except Exception:
            return None, f"Invalid timestamp: {timestamp_raw}"

        event_type = _pick(row, FIELD_ALIASES["event_type"])
        if not event_type:
            return None, "Missing event_type/event"
        event_type = str(event_type).strip().lower().replace(" ", "_")

        user_name = _pick(row, FIELD_ALIASES["user_name"])
        source_ip = _pick(row, FIELD_ALIASES["source_ip"])
        destination_ip = _pick(row, FIELD_ALIASES["destination_ip"])
        asset_name = _pick(row, FIELD_ALIASES["asset"])
        asset_id = self._resolve_asset_id(_pick(row, FIELD_ALIASES["asset_id"]), asset_name)
        location = _pick(row, FIELD_ALIASES["location"])
        severity = _severity(_pick(row, FIELD_ALIASES["severity"]))
        message = _pick(row, FIELD_ALIASES["message"]) or f"{event_type} event"

        fp_payload = {
            "timestamp": iso(ts),
            "user_name": user_name,
            "event_type": event_type,
            "source_ip": source_ip,
            "message": message,
        }
        record = {
            "timestamp": iso(ts),
            "user_name": str(user_name) if user_name else None,
            "event_type": event_type,
            "source_ip": str(source_ip) if source_ip else None,
            "destination_ip": str(destination_ip) if destination_ip else None,
            "asset_id": asset_id,
            "location": str(location) if location else None,
            "severity": severity,
            "message": str(message),
            "raw_data": row,
            "is_demo": is_demo,
            "fingerprint": fingerprint(fp_payload),
        }
        return record, None

    def normalize_many(self, rows: List[Dict[str, Any]], is_demo: bool = False) -> Dict[str, Any]:
        accepted: List[Dict[str, Any]] = []
        errors: List[Dict[str, Any]] = []
        for index, row in enumerate(rows):
            record, error = self.normalize_row(row, is_demo=is_demo)
            if error:
                errors.append({"index": index, "error": error})
            else:
                accepted.append(record)
        return {"accepted": accepted, "errors": errors}
