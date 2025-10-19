"""
Trunks router - CRUD operations for trunks
"""
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import verify_hmac
from app.models import APIUser, Trunk
from app.schemas import TrunkCreate, TrunkResponse, TrunkUpdate

router = APIRouter()


@router.get("", response_model=List[TrunkResponse])
async def list_trunks(
    db: Session = Depends(get_db),
    api_user: APIUser = Depends(verify_hmac),
):
    """List all trunks"""
    trunks = db.query(Trunk).order_by(Trunk.priority).all()
    return trunks


@router.post("", response_model=TrunkResponse, status_code=status.HTTP_201_CREATED)
async def create_trunk(
    trunk_data: TrunkCreate,
    db: Session = Depends(get_db),
    api_user: APIUser = Depends(verify_hmac),
):
    """Create new trunk"""
    trunk = Trunk(
        id=uuid4(),
        name=trunk_data.name,
        host=trunk_data.host,
        username=trunk_data.username,
        secret=trunk_data.secret,
        priority=trunk_data.priority,
        enabled=trunk_data.enabled,
    )
    db.add(trunk)
    db.commit()
    db.refresh(trunk)
    return trunk


@router.get("/{trunk_id}", response_model=TrunkResponse)
async def get_trunk(
    trunk_id: str,
    db: Session = Depends(get_db),
    api_user: APIUser = Depends(verify_hmac),
):
    """Get trunk by ID"""
    trunk = db.query(Trunk).filter(Trunk.id == trunk_id).first()
    if not trunk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trunk not found",
        )
    return trunk


@router.put("/{trunk_id}", response_model=TrunkResponse)
async def update_trunk(
    trunk_id: str,
    trunk_data: TrunkUpdate,
    db: Session = Depends(get_db),
    api_user: APIUser = Depends(verify_hmac),
):
    """Update trunk"""
    trunk = db.query(Trunk).filter(Trunk.id == trunk_id).first()
    if not trunk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trunk not found",
        )

    if trunk_data.name is not None:
        trunk.name = trunk_data.name
    if trunk_data.host is not None:
        trunk.host = trunk_data.host
    if trunk_data.username is not None:
        trunk.username = trunk_data.username
    if trunk_data.secret is not None:
        trunk.secret = trunk_data.secret
    if trunk_data.priority is not None:
        trunk.priority = trunk_data.priority
    if trunk_data.enabled is not None:
        trunk.enabled = trunk_data.enabled

    db.commit()
    db.refresh(trunk)
    return trunk


@router.delete("/{trunk_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trunk(
    trunk_id: str,
    db: Session = Depends(get_db),
    api_user: APIUser = Depends(verify_hmac),
):
    """Delete trunk"""
    trunk = db.query(Trunk).filter(Trunk.id == trunk_id).first()
    if not trunk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trunk not found",
        )

    db.delete(trunk)
    db.commit()
