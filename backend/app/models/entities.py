# ORM-style documentation models (persistence is via the Supabase client).

from typing import Any, Optional

from pydantic import BaseModel, Field


class Profile(BaseModel):
    id: str
    full_name: str
    email: str
    role: str


class SecurityLog(BaseModel):
    id: str
    timestamp: str
    user_name: Optional[str] = None
    event_type: str
    raw_data: dict[str, Any] = Field(default_factory=dict)


class Incident(BaseModel):
    id: str
    incident_number: str
    title: str
    risk_score: int
    status: str
