"""Persist normalized logs. Never executes commands from log content."""

import csv
import io
import json
from typing import Any, Dict, List, Tuple

from app.config import get_settings
from app.database import security_logs as logs_repo
from app.services.normalization_service import NormalizationService
from app.utils.errors import AppError

ALLOWED_EVENT_CHARS = set("abcdefghijklmnopqrstuvwxyz0123456789_-. ")


def _safe_json_load(raw: str) -> Any:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AppError(f"Invalid JSON: {exc.msg}", status_code=400, code="invalid_json") from exc


class IngestionService:
    def __init__(self) -> None:
        self.normalizer = NormalizationService()

    def _dedupe(self, records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
        seen = set()
        unique = []
        skipped = 0
        existing = {
            row["fingerprint"]
            for row in logs_repo.select(columns="fingerprint", limit=5000)
            if row.get("fingerprint")
        }
        for record in records:
            fp = record.get("fingerprint")
            if fp in seen or fp in existing:
                skipped += 1
                continue
            seen.add(fp)
            unique.append(record)
        return unique, skipped

    def ingest_rows(self, rows: List[Dict[str, Any]], is_demo: bool = False) -> Dict[str, Any]:
        if not rows:
            raise AppError("No log records supplied", status_code=400, code="empty_upload")
        result = self.normalizer.normalize_many(rows, is_demo=is_demo)
        unique, duplicates = self._dedupe(result["accepted"])
        inserted = []
        if unique:
            inserted = logs_repo.insert(unique)
        return {
            "inserted": inserted,
            "inserted_count": len(inserted),
            "duplicate_count": duplicates,
            "error_count": len(result["errors"]),
            "errors": result["errors"][:50],
        }

    def parse_upload(self, filename: str, content: bytes) -> List[Dict[str, Any]]:
        settings = get_settings()
        if len(content) > settings.max_upload_bytes:
            raise AppError("Upload exceeds size limit", status_code=413, code="upload_too_large")
        if not content:
            raise AppError("Empty upload", status_code=400, code="empty_upload")
        name = (filename or "").lower()
        text = content.decode("utf-8-sig", errors="replace")
        if name.endswith(".csv") or ("," in text.splitlines()[0] and not text.lstrip().startswith(("[", "{"))):
            reader = csv.DictReader(io.StringIO(text))
            if not reader.fieldnames:
                raise AppError("CSV is missing a header row", status_code=400, code="invalid_csv")
            return [dict(row) for row in reader if any(v for v in row.values())]
        payload = _safe_json_load(text)
        if isinstance(payload, dict):
            if "logs" in payload and isinstance(payload["logs"], list):
                return payload["logs"]
            return [payload]
        if isinstance(payload, list):
            return payload
        raise AppError("JSON must be an object or array of log records", status_code=400, code="invalid_json")
