from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]


class LoginRequest(BaseModel):
    email: str
    password: str


class ProfileOut(BaseModel):
    id: str
    full_name: str
    email: str
    role: str
    created_at: Optional[str] = None


class LogIn(BaseModel):
    timestamp: Optional[str] = None
    user_name: Optional[str] = None
    user: Optional[str] = None
    event_type: Optional[str] = None
    event: Optional[str] = None
    source_ip: Optional[str] = None
    destination_ip: Optional[str] = None
    asset_id: Optional[str] = None
    asset: Optional[str] = None
    location: Optional[str] = None
    severity: Optional[str] = None
    message: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None

    model_config = {"extra": "allow"}


class LogOut(BaseModel):
    id: str
    timestamp: str
    user_name: Optional[str] = None
    event_type: str
    source_ip: Optional[str] = None
    destination_ip: Optional[str] = None
    asset_id: Optional[str] = None
    location: Optional[str] = None
    severity: str
    message: Optional[str] = None
    raw_data: Dict[str, Any] = Field(default_factory=dict)
    is_demo: bool = False
    created_at: Optional[str] = None


class IncidentIn(BaseModel):
    title: str
    description: Optional[str] = None
    severity: str = "medium"
    affected_user: Optional[str] = None
    affected_asset: Optional[str] = None


class IncidentPatch(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    severity: Optional[str] = None


class IncidentOut(BaseModel):
    id: str
    incident_number: str
    title: str
    description: Optional[str] = None
    severity: str
    risk_score: int
    confidence_score: int
    status: str
    detected_at: str
    resolved_at: Optional[str] = None
    affected_user: Optional[str] = None
    affected_asset: Optional[str] = None
    ai_summary: Optional[str] = None
    potential_impact: Any = None
    risk_factors: Any = None
    is_demo: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class AssetOut(BaseModel):
    id: str
    asset_name: str
    asset_type: str
    ip_address: Optional[str] = None
    hostname: Optional[str] = None
    status: str
    owner: Optional[str] = None
    risk_level: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ThreatIntelIn(BaseModel):
    indicator_type: str
    indicator_value: str
    reputation: str = "unknown"
    confidence: int = 50
    source: str = "internal"
    details: Dict[str, Any] = Field(default_factory=dict)


class ThreatIntelOut(ThreatIntelIn):
    id: str
    created_at: Optional[str] = None


class RecommendationOut(BaseModel):
    id: str
    incident_id: str
    action_type: str
    description: str
    priority: str
    requires_approval: bool
    status: str
    created_at: Optional[str] = None


class InvestigationOut(BaseModel):
    id: str
    incident_id: str
    investigation_status: str
    ai_assessment: Dict[str, Any]
    reasoning_summary: Optional[str] = None
    evidence: Any = None
    attack_pattern: Optional[str] = None
    potential_impact: Any = None
    confidence_score: int
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
    provider: Optional[str] = None


class DashboardStats(BaseModel):
    total_events: int
    active_incidents: int
    critical_incidents: int
    high_risk_incidents: int
    resolved_incidents: int
    incidents_by_severity: Dict[str, int]
    incidents_over_time: List[Dict[str, Any]]
    event_types: List[Dict[str, Any]]
    risk_distribution: List[Dict[str, Any]]
    recent_incidents: List[Dict[str, Any]]
    recent_events: List[Dict[str, Any]]
    system_status: Dict[str, Any]


class HealthOut(BaseModel):
    status: str
    supabase: str
    ai: str
    demo_mode: bool
    timestamp: datetime
