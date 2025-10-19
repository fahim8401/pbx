"""
Plan Templates router - CRUD operations for plan templates
"""
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import verify_hmac
from app.models import APIUser, PlanTemplate
from app.schemas import (
    PlanTemplateCreate,
    PlanTemplateResponse,
    PlanTemplateUpdate,
)

router = APIRouter()


@router.get("", response_model=List[PlanTemplateResponse])
async def list_plan_templates(
    db: Session = Depends(get_db),
    api_user: APIUser = Depends(verify_hmac),
):
    """List all plan templates"""
    templates = db.query(PlanTemplate).all()
    return templates


@router.post("", response_model=PlanTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_plan_template(
    template_data: PlanTemplateCreate,
    db: Session = Depends(get_db),
    api_user: APIUser = Depends(verify_hmac),
):
    """Create new plan template"""
    template = PlanTemplate(
        id=uuid4(),
        name=template_data.name,
        description=template_data.description,
        limits_json=template_data.limits,
        routing_json=template_data.routing,
        propagate_updates=template_data.propagate_updates,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.get("/{template_id}", response_model=PlanTemplateResponse)
async def get_plan_template(
    template_id: str,
    db: Session = Depends(get_db),
    api_user: APIUser = Depends(verify_hmac),
):
    """Get plan template by ID"""
    template = db.query(PlanTemplate).filter(PlanTemplate.id == template_id).first()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan template not found",
        )
    return template


@router.put("/{template_id}", response_model=PlanTemplateResponse)
async def update_plan_template(
    template_id: str,
    template_data: PlanTemplateUpdate,
    db: Session = Depends(get_db),
    api_user: APIUser = Depends(verify_hmac),
):
    """Update plan template"""
    template = db.query(PlanTemplate).filter(PlanTemplate.id == template_id).first()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan template not found",
        )

    if template_data.name is not None:
        template.name = template_data.name
    if template_data.description is not None:
        template.description = template_data.description
    if template_data.limits is not None:
        template.limits_json = template_data.limits
    if template_data.routing is not None:
        template.routing_json = template_data.routing
    if template_data.propagate_updates is not None:
        template.propagate_updates = template_data.propagate_updates

    db.commit()
    db.refresh(template)
    return template


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan_template(
    template_id: str,
    db: Session = Depends(get_db),
    api_user: APIUser = Depends(verify_hmac),
):
    """Delete plan template"""
    template = db.query(PlanTemplate).filter(PlanTemplate.id == template_id).first()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan template not found",
        )

    # Check if any tenants are using this template
    if template.tenants:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete template in use by tenants",
        )

    db.delete(template)
    db.commit()
