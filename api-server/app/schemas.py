"""
Pydantic schemas for API requests/responses
"""
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# Tenant schemas
class TenantBase(BaseModel):
    """Base tenant schema"""

    name: str = Field(..., min_length=1, max_length=255)
    domain: str = Field(..., min_length=1, max_length=255)


class TenantCreate(TenantBase):
    """Tenant creation schema"""

    email: EmailStr
    plan_template_id: Optional[UUID] = None
    limits: Optional[Dict] = None


class TenantUpdate(BaseModel):
    """Tenant update schema"""

    action: str = Field(..., pattern="^(suspend|resume|update_limits)$")
    limits: Optional[Dict] = None


class TenantResponse(TenantBase):
    """Tenant response schema"""

    id: UUID
    status: str
    billing_mode: str
    plan_template_id: Optional[UUID]
    created_at: datetime

    class Config:
        from_attributes = True


class TenantCreateResponse(BaseModel):
    """Tenant creation response"""

    id: UUID
    domain: str
    portal_url: str
    admin_user: str
    admin_pass: str


class TenantSummary(BaseModel):
    """Tenant summary schema"""

    id: UUID
    name: str
    domain: str
    status: str
    limits: Dict
    usage: Dict
    counts: Dict


# Plan Template schemas
class PlanTemplateBase(BaseModel):
    """Base plan template schema"""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class PlanTemplateCreate(PlanTemplateBase):
    """Plan template creation schema"""

    limits: Dict = Field(default_factory=dict)
    routing: Dict = Field(default_factory=dict)
    propagate_updates: bool = False


class PlanTemplateUpdate(PlanTemplateBase):
    """Plan template update schema"""

    limits: Optional[Dict] = None
    routing: Optional[Dict] = None
    propagate_updates: Optional[bool] = None


class PlanTemplateResponse(PlanTemplateBase):
    """Plan template response schema"""

    id: UUID
    limits_json: Dict
    routing_json: Dict
    propagate_updates: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Extension schemas
class ExtensionBase(BaseModel):
    """Base extension schema"""

    username: str = Field(..., min_length=3, max_length=100)


class ExtensionCreate(ExtensionBase):
    """Extension creation schema"""

    password: str = Field(..., min_length=8)
    webrtc: bool = True
    voicemail_email: Optional[EmailStr] = None


class ExtensionResponse(ExtensionBase):
    """Extension response schema"""

    id: UUID
    tenant_id: UUID
    webrtc: bool
    voicemail_email: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# DID schemas
class DIDBase(BaseModel):
    """Base DID schema"""

    e164: str = Field(..., pattern=r"^\+?[1-9]\d{1,14}$")


class DIDCreate(DIDBase):
    """DID creation schema"""

    pass


class DIDAllocate(BaseModel):
    """DID allocation schema"""

    tenant_id: UUID
    dids: List[str]


class DIDResponse(DIDBase):
    """DID response schema"""

    id: UUID
    tenant_id: Optional[UUID]
    status: str
    routing_json: Dict
    created_at: datetime

    class Config:
        from_attributes = True


# Trunk schemas
class TrunkBase(BaseModel):
    """Base trunk schema"""

    name: str = Field(..., min_length=1, max_length=255)
    host: str = Field(..., min_length=1)


class TrunkCreate(TrunkBase):
    """Trunk creation schema"""

    username: Optional[str] = None
    secret: Optional[str] = None
    priority: int = Field(default=100, ge=1, le=999)
    enabled: bool = True


class TrunkUpdate(BaseModel):
    """Trunk update schema"""

    name: Optional[str] = None
    host: Optional[str] = None
    username: Optional[str] = None
    secret: Optional[str] = None
    priority: Optional[int] = None
    enabled: Optional[bool] = None


class TrunkResponse(TrunkBase):
    """Trunk response schema"""

    id: UUID
    username: Optional[str]
    priority: int
    enabled: bool
    created_at: datetime

    class Config:
        from_attributes = True


# IVR schemas
class IVRTreeCreate(BaseModel):
    """IVR tree creation schema"""

    name: str = Field(..., min_length=1, max_length=255)
    json: Dict


class IVRTreeUpdate(BaseModel):
    """IVR tree update schema"""

    name: Optional[str] = None
    json: Optional[Dict] = None


class IVRTreeResponse(BaseModel):
    """IVR tree response schema"""

    id: UUID
    tenant_id: UUID
    name: str
    json: Dict
    created_at: datetime

    class Config:
        from_attributes = True


# CDR schemas
class CDRFilter(BaseModel):
    """CDR filter parameters"""

    tenant_id: Optional[UUID] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    disposition: Optional[str] = None
    page: int = Field(default=1, ge=1)
    size: int = Field(default=50, ge=1, le=1000)


class CDRResponse(BaseModel):
    """CDR response schema"""

    id: UUID
    tenant_id: UUID
    src: str
    dst: str
    started_at: datetime
    ended_at: Optional[datetime]
    billsec: int
    disposition: str
    cost: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


# Usage schemas
class UsageMetricsRequest(BaseModel):
    """Usage metrics request schema"""

    tenant_id: UUID
    from_date: datetime
    to_date: datetime


class UsageMetricsResponse(BaseModel):
    """Usage metrics response schema"""

    tenant_id: UUID
    from_date: datetime
    to_date: datetime
    minutes_in: int
    minutes_out: int
    storage_gb: float
    sms_count: int


# Recording schemas
class RecordingResponse(BaseModel):
    """Recording response schema"""

    id: UUID
    tenant_id: UUID
    call_id: str
    path: str
    duration: int
    size_bytes: int
    created_at: datetime

    class Config:
        from_attributes = True


class RecordingPresignRequest(BaseModel):
    """Recording presign request schema"""

    recording_id: UUID


class RecordingPresignResponse(BaseModel):
    """Recording presign response schema"""

    url: str
    expires_in: int


# Auth schemas
class LoginRequest(BaseModel):
    """Login request schema"""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Token response schema"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class PasswordResetRequest(BaseModel):
    """Password reset request schema"""

    tenant_id: UUID


class PasswordResetResponse(BaseModel):
    """Password reset response schema"""

    admin_user: str
    admin_pass: str


# Health schema
class HealthResponse(BaseModel):
    """Health check response schema"""

    status: str = "ok"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
