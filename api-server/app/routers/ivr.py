"""
IVR router - CRUD operations for IVR trees
"""
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import verify_hmac
from app.models import APIUser, IVRTree
from app.schemas import IVRTreeCreate, IVRTreeResponse, IVRTreeUpdate

router = APIRouter()


@router.get("", response_model=List[IVRTreeResponse])
async def list_ivr_trees(
    tenant_id: str = None,
    db: Session = Depends(get_db),
    api_user: APIUser = Depends(verify_hmac),
):
    """List IVR trees, optionally filtered by tenant"""
    query = db.query(IVRTree)
    if tenant_id:
        query = query.filter(IVRTree.tenant_id == tenant_id)
    return query.all()


@router.post("", response_model=IVRTreeResponse, status_code=status.HTTP_201_CREATED)
async def create_ivr_tree(
    tenant_id: str,
    ivr_data: IVRTreeCreate,
    db: Session = Depends(get_db),
    api_user: APIUser = Depends(verify_hmac),
):
    """Create new IVR tree"""
    ivr = IVRTree(
        id=uuid4(),
        tenant_id=tenant_id,
        name=ivr_data.name,
        json=ivr_data.json,
    )
    db.add(ivr)
    db.commit()
    db.refresh(ivr)
    return ivr


@router.get("/{ivr_id}", response_model=IVRTreeResponse)
async def get_ivr_tree(
    ivr_id: str,
    db: Session = Depends(get_db),
    api_user: APIUser = Depends(verify_hmac),
):
    """Get IVR tree by ID"""
    ivr = db.query(IVRTree).filter(IVRTree.id == ivr_id).first()
    if not ivr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="IVR tree not found",
        )
    return ivr


@router.put("/{ivr_id}", response_model=IVRTreeResponse)
async def update_ivr_tree(
    ivr_id: str,
    ivr_data: IVRTreeUpdate,
    db: Session = Depends(get_db),
    api_user: APIUser = Depends(verify_hmac),
):
    """Update IVR tree"""
    ivr = db.query(IVRTree).filter(IVRTree.id == ivr_id).first()
    if not ivr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="IVR tree not found",
        )

    if ivr_data.name is not None:
        ivr.name = ivr_data.name
    if ivr_data.json is not None:
        ivr.json = ivr_data.json

    db.commit()
    db.refresh(ivr)
    return ivr


@router.delete("/{ivr_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ivr_tree(
    ivr_id: str,
    db: Session = Depends(get_db),
    api_user: APIUser = Depends(verify_hmac),
):
    """Delete IVR tree"""
    ivr = db.query(IVRTree).filter(IVRTree.id == ivr_id).first()
    if not ivr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="IVR tree not found",
        )

    db.delete(ivr)
    db.commit()
