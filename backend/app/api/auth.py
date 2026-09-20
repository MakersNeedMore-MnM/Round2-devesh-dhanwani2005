from typing import Any, Dict

from fastapi import APIRouter, Depends

from app.schemas.common import LoginRequest, ProfileOut
from app.services.auth_service import get_current_user, login

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/login")
def auth_login(payload: LoginRequest):
    return login(payload.email, payload.password)


@router.post("/logout")
def auth_logout(_: Dict[str, Any] = Depends(get_current_user)):
    return {"status": "signed_out"}


@router.get("/me", response_model=ProfileOut)
def me(user: Dict[str, Any] = Depends(get_current_user)):
    return user
