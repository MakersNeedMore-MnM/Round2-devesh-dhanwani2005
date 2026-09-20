from typing import Any, Dict

from fastapi import APIRouter, Depends

from app.database import assets as assets_repo
from app.services.auth_service import get_current_user
from app.utils.errors import AppError, NOT_FOUND

router = APIRouter(prefix="/api/assets", tags=["Assets"])


@router.get("")
def list_assets(_: Dict[str, Any] = Depends(get_current_user)):
    return assets_repo.select(order="asset_name", desc=False, limit=200)


@router.get("/{asset_id}")
def get_asset(asset_id: str, _: Dict[str, Any] = Depends(get_current_user)):
    row = assets_repo.get(asset_id)
    if not row:
        raise AppError("Asset not found", status_code=NOT_FOUND, code="not_found")
    return row
