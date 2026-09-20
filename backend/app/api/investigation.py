from typing import Any, Dict

from fastapi import APIRouter, Depends

from app.services.auth_service import get_current_user
from app.services.demo_service import DemoService

router = APIRouter(prefix="/api/demo", tags=["Demo"])
demo = DemoService()


@router.post("/load")
def load_demo(user: Dict[str, Any] = Depends(get_current_user)):
    return demo.load_attack(user)


@router.post("/reset")
def reset_demo(user: Dict[str, Any] = Depends(get_current_user)):
    return {"status": "reset", **demo.reset(), "by": user.get("email")}
