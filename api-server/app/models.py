"""
SQLAlchemy database models
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db import Base


class TenantStatus(PyEnum):
    """Tenant status enum"""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class BillingMode(PyEnum):
    """Billing mode enum"""

    POSTPAID = "postpaid"
    PREPAID = "prepaid"


class DIDStatus(PyEnum):
    """DID status enum"""

    FREE = "free"
    ASSIGNED = "assigned"
    RESERVED = "reserved"


class UserRole(PyEnum):
    """User role enum"""

    SUPERADMIN = "superadmin"
    TENANT_ADMIN = "tenant_admin"
    MANAGER = "manager"
    AGENT = "agent"


class APIUserRole(PyEnum):
    """API user role enum"""

    WHMCS = "whmcs"
    ADMIN = "admin"
    SYSTEM = "system"


class Tenant(Base):
    """Tenant/Customer table"""

    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    domain = Column(String(255), unique=True, nullable=False)
    status = Column(Enum(TenantStatus), default=TenantStatus.ACTIVE, nullable=False)
    limits_json = Column(JSON, default={})
    billing_mode = Column(Enum(BillingMode), default=BillingMode.POSTPAID)
    plan_template_id = Column(UUID(as_uuid=True), ForeignKey("plan_templates.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    plan_template = relationship("PlanTemplate", back_populates="tenants")
    extensions = relationship("Extension", back_populates="tenant", cascade="all, delete-orphan")
    dids = relationship("DID", back_populates="tenant")
    cdr = relationship("CDR", back_populates="tenant")
    recordings = relationship("Recording", back_populates="tenant")
    ivr_trees = relationship("IVRTree", back_populates="tenant", cascade="all, delete-orphan")
    usage_snapshots = relationship("UsageSnapshot", back_populates="tenant")


class PlanTemplate(Base):
    """Plan template table"""

    __tablename__ = "plan_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    limits_json = Column(JSON, default={})
    routing_json = Column(JSON, default={})
    propagate_updates = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenants = relationship("Tenant", back_populates="plan_template")


class Extension(Base):
    """Extension/User table"""

    __tablename__ = "extensions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    username = Column(String(100), nullable=False, index=True)
    secret_hash = Column(String(255), nullable=False)
    webrtc = Column(Boolean, default=True)
    forwarding_json = Column(JSON, default={})
    voicemail_email = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="extensions")


class DID(Base):
    """DID inventory table"""

    __tablename__ = "dids"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    e164 = Column(String(20), unique=True, nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    status = Column(Enum(DIDStatus), default=DIDStatus.FREE, nullable=False)
    routing_json = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="dids")


class Trunk(Base):
    """Trunk configuration table"""

    __tablename__ = "trunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    host = Column(String(255), nullable=False)
    username = Column(String(100))
    secret = Column(String(255))
    priority = Column(Integer, default=100)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    cdr = relationship("CDR", back_populates="trunk")


class CDR(Base):
    """Call Detail Records table"""

    __tablename__ = "cdr"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    src = Column(String(100), nullable=False)
    dst = Column(String(100), nullable=False)
    started_at = Column(DateTime, nullable=False, index=True)
    ended_at = Column(DateTime)
    billsec = Column(Integer, default=0)
    disposition = Column(String(50))
    trunk_id = Column(UUID(as_uuid=True), ForeignKey("trunks.id"), nullable=True)
    cost = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="cdr")
    trunk = relationship("Trunk", back_populates="cdr")


class Recording(Base):
    """Call recordings table"""

    __tablename__ = "recordings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    call_id = Column(String(255), nullable=False)
    path = Column(String(500), nullable=False)
    duration = Column(Integer, default=0)
    size_bytes = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="recordings")


class IVRTree(Base):
    """IVR tree configurations table"""

    __tablename__ = "ivr_trees"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    name = Column(String(255), nullable=False)
    json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="ivr_trees")


class UsageSnapshot(Base):
    """Usage metrics snapshots table"""

    __tablename__ = "usage_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    from_ts = Column(DateTime, nullable=False)
    to_ts = Column(DateTime, nullable=False)
    minutes_in = Column(Integer, default=0)
    minutes_out = Column(Integer, default=0)
    storage_gb = Column(Float, default=0.0)
    sms_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="usage_snapshots")


class APIUser(Base):
    """API users for HMAC authentication table"""

    __tablename__ = "api_users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), unique=True, nullable=False, index=True)
    secret_hash = Column(String(255), nullable=False)
    role = Column(Enum(APIUserRole), nullable=False)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class PortalUser(Base):
    """Portal users for JWT authentication table"""

    __tablename__ = "portal_users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    pass_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
