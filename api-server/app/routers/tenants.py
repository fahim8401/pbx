"""
Tenants router - CRUD operations for tenants
"""
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import generate_random_password, hash_password, verify_hmac
from app.models import APIUser, PortalUser, Tenant, TenantStatus, UserRole
from app.schemas import (
    PasswordResetRequest,
    PasswordResetResponse,
    TenantCreate,
    TenantCreateResponse,
    TenantResponse,
    TenantSummary,
    TenantUpdate,
)

router = APIRouter()


@router.post("", response_model=TenantCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant_data: TenantCreate,
    db: Session = Depends(get_db),
    api_user: APIUser = Depends(verify_hmac),
):
    """Create new tenant"""
    # Check if domain already exists
    existing = db.query(Tenant).filter(Tenant.domain == tenant_data.domain).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Domain already exists",
        )

    # Create tenant
    tenant = Tenant(
        id=uuid4(),
        name=tenant_data.name,
        domain=tenant_data.domain,
        status=TenantStatus.ACTIVE,
        plan_template_id=tenant_data.plan_template_id,
        limits_json=tenant_data.limits or {},
    )
    db.add(tenant)

    # Create portal admin user
    admin_password = generate_random_password()
    portal_user = PortalUser(
        id=uuid4(),
        tenant_id=tenant.id,
        email=tenant_data.email,
        pass_hash=hash_password(admin_password),
        role=UserRole.TENANT_ADMIN,
    )
    db.add(portal_user)

    db.commit()
    db.refresh(tenant)

    # Generate portal URL
    portal_url = f"https://portal.hplinkpbx.com/{tenant.domain}"

    return TenantCreateResponse(
        id=tenant.id,
        domain=tenant.domain,
        portal_url=portal_url,
        admin_user=tenant_data.email,
        admin_pass=admin_password,
    )


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: str,
    db: Session = Depends(get_db),
    api_user: APIUser = Depends(verify_hmac),
):
    """Get tenant by ID"""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )
    return tenant


@router.patch("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: str,
    update_data: TenantUpdate,
    db: Session = Depends(get_db),
    api_user: APIUser = Depends(verify_hmac),
):
    """Update tenant (suspend/resume/update_limits)"""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    if update_data.action == "suspend":
        tenant.status = TenantStatus.SUSPENDED
    elif update_data.action == "resume":
        tenant.status = TenantStatus.ACTIVE
    elif update_data.action == "update_limits":
        if update_data.limits:
            tenant.limits_json = update_data.limits

    db.commit()
    db.refresh(tenant)
    return tenant


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(
    tenant_id: str,
    db: Session = Depends(get_db),
    api_user: APIUser = Depends(verify_hmac),
):
    """Soft delete tenant"""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    tenant.status = TenantStatus.DELETED
    db.commit()


@router.get("/{tenant_id}/summary", response_model=TenantSummary)
async def get_tenant_summary(
    tenant_id: str,
    db: Session = Depends(get_db),
    api_user: APIUser = Depends(verify_hmac),
):
    """Get tenant summary with usage and counts"""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    # Get counts
    from app.models import DID, Extension

    extensions_count = db.query(Extension).filter(Extension.tenant_id == tenant_id).count()
    dids_count = db.query(DID).filter(DID.tenant_id == tenant_id).count()

    return TenantSummary(
        id=tenant.id,
        name=tenant.name,
        domain=tenant.domain,
        status=tenant.status.value,
        limits=tenant.limits_json,
        usage={
            "minutes_in": 0,
            "minutes_out": 0,
            "storage_gb": 0,
        },
        counts={
            "extensions": extensions_count,
            "dids": dids_count,
        },
    )


@router.post("/{tenant_id}/reset-password", response_model=PasswordResetResponse)
async def reset_password(
    tenant_id: str,
    db: Session = Depends(get_db),
    api_user: APIUser = Depends(verify_hmac),
):
    """Reset portal admin password"""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    # Get admin user
    admin = (
        db.query(PortalUser)
        .filter(
            PortalUser.tenant_id == tenant_id,
            PortalUser.role == UserRole.TENANT_ADMIN,
        )
        .first()
    )

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin user not found",
        )

    # Generate new password
    new_password = generate_random_password()
    admin.pass_hash = hash_password(new_password)
    db.commit()

    return PasswordResetResponse(
        admin_user=admin.email,
        admin_pass=new_password,
    )
