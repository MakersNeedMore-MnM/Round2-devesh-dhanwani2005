from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, File, UploadFile

from app.database import security_logs as logs_repo
from app.services.auth_service import get_current_user
from app.services.ingestion_service import IngestionService
from app.services.pipeline_service import PipelineService
from app.utils.errors import AppError, NOT_FOUND
from app.utils.lookups import query_logs

router = APIRouter(prefix="/api/logs", tags=["Logs"])
ingestion = IngestionService()
pipeline = PipelineService()


@router.get("", response_model=List[Dict[str, Any]])
def list_logs(
    search: Optional[str] = None,
    severity: Optional[str] = None,
    event_type: Optional[str] = None,
    user_name: Optional[str] = None,
    _: Dict[str, Any] = Depends(get_current_user),
):
    return query_logs(search=search, severity=severity, event_type=event_type, user_name=user_name)


@router.get("/{log_id}")
def get_log(log_id: str, _: Dict[str, Any] = Depends(get_current_user)):
    row = logs_repo.get(log_id)
    if not row:
        raise AppError("Log not found", status_code=NOT_FOUND, code="not_found")
    return row


@router.post("")
def create_logs(payload: Any = Body(...), _: Dict[str, Any] = Depends(get_current_user)):
    rows = payload if isinstance(payload, list) else [payload]
    if not isinstance(rows, list):
        raise AppError("Body must be a log object or array", status_code=400, code="invalid_json")
    ingested = ingestion.ingest_rows(rows)
    incidents = pipeline.process_new_ids([row["id"] for row in ingested.get("inserted") or []])
    return {**ingested, "incidents": incidents}


@router.post("/upload")
async def upload_logs(
    file: UploadFile = File(...),
    _: Dict[str, Any] = Depends(get_current_user),
):
    content = await file.read()
    rows = ingestion.parse_upload(file.filename or "upload.json", content)
    ingested = ingestion.ingest_rows(rows)
    incidents = pipeline.process_new_ids([row["id"] for row in ingested.get("inserted") or []])
    return {**ingested, "incidents": incidents, "filename": file.filename}
