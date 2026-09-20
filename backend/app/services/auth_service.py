from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import Depends, Header
from jose import JWTError, jwt
from supabase import create_client

from app.config import get_settings
from app.database import profiles as profiles_repo
from app.utils.errors import AppError, FORBIDDEN, UNAUTHORIZED

DEMO_PROFILE_FALLBACK = {
    "id": "33333333-3333-4333-8333-333333333333",
    "full_name": "Sofia Alvarez",
    "email": "sofia.alvarez@cybersentinel.demo",
    "role": "analyst",
}


def _demo_token(profile: Dict[str, Any]) -> str:
    settings = get_settings()
    payload = {
        "sub": profile["id"],
        "email": profile["email"],
        "role": profile["role"],
        "full_name": profile.get("full_name"),
        "typ": "demo",
        "exp": datetime.now(timezone.utc) + timedelta(hours=12),
    }
    return jwt.encode(payload, settings.demo_jwt_secret, algorithm="HS256")


def login(email: str, password: str) -> Dict[str, Any]:
    settings = get_settings()
    email = email.strip().lower()
    if settings.demo_mode and email == settings.demo_analyst_email.lower() and password == settings.demo_analyst_password:
        profile = profiles_repo.select(filters={"email": settings.demo_analyst_email}, limit=1)
        user = profile[0] if profile else {**DEMO_PROFILE_FALLBACK, "email": settings.demo_analyst_email}
        return {"access_token": _demo_token(user), "token_type": "bearer", "user": user}

    if settings.supabase_url and settings.supabase_anon_key:
        try:
            client = create_client(settings.supabase_url, settings.supabase_anon_key)
            result = client.auth.sign_in_with_password({"email": email, "password": password})
            session = result.session
            auth_user = result.user
            if not session or not auth_user:
                raise AppError("Invalid credentials", status_code=UNAUTHORIZED, code="unauthorized")
            profile_rows = profiles_repo.select(filters={"id": auth_user.id}, limit=1)
            if not profile_rows:
                profile_rows = profiles_repo.select(filters={"email": email}, limit=1)
            profile = profile_rows[0] if profile_rows else {
                "id": auth_user.id,
                "full_name": email.split("@")[0],
                "email": email,
                "role": "analyst",
            }
            return {
                "access_token": session.access_token,
                "token_type": "bearer",
                "user": profile,
            }
        except AppError:
            raise
        except Exception:
            raise AppError("Authentication failed", status_code=UNAUTHORIZED, code="unauthorized") from None

    raise AppError("Invalid credentials or auth is not configured", status_code=UNAUTHORIZED, code="unauthorized")


def decode_token(token: str) -> Dict[str, Any]:
    settings = get_settings()
    try:
        demo = jwt.decode(token, settings.demo_jwt_secret, algorithms=["HS256"])
        if demo.get("typ") == "demo":
            return demo
    except JWTError:
        pass

    if settings.supabase_jwt_secret:
        try:
            return jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                options={"verify_aud": False},
            )
        except JWTError as exc:
            raise AppError("Invalid or expired session", status_code=UNAUTHORIZED, code="unauthorized") from exc

    if settings.supabase_url and settings.supabase_anon_key:
        try:
            client = create_client(settings.supabase_url, settings.supabase_anon_key)
            user = client.auth.get_user(token)
            if not user or not user.user:
                raise AppError("Invalid or expired session", status_code=UNAUTHORIZED, code="unauthorized")
            return {"sub": user.user.id, "email": user.user.email, "role": (user.user.user_metadata or {}).get("role")}
        except AppError:
            raise
        except Exception as exc:
            raise AppError("Invalid or expired session", status_code=UNAUTHORIZED, code="unauthorized") from exc

    raise AppError("Invalid or expired session", status_code=UNAUTHORIZED, code="unauthorized")


def get_current_user(authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise AppError("Sign in required", status_code=UNAUTHORIZED, code="unauthorized")
    token = authorization.split(" ", 1)[1].strip()
    claims = decode_token(token)
    user_id = claims.get("sub")
    email = claims.get("email")
    profile = None
    if user_id:
        profile = profiles_repo.get(user_id)
    if not profile and email:
        rows = profiles_repo.select(filters={"email": email}, limit=1)
        profile = rows[0] if rows else None
    if not profile:
        profile = {
            "id": user_id,
            "full_name": claims.get("full_name") or (email or "analyst"),
            "email": email,
            "role": claims.get("role") or "analyst",
        }
    if profile.get("role") not in {"analyst", "senior_analyst", "admin"}:
        raise AppError("Insufficient role", status_code=FORBIDDEN, code="forbidden")
    return profile


def require_roles(*roles: str):
    def checker(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        if user.get("role") not in roles:
            raise AppError("Insufficient role", status_code=FORBIDDEN, code="forbidden")
        return user

    return checker
