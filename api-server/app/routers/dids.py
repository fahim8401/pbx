"""
DIDs router - DID inventory and allocation
"""
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import verify_hmac
from app.models import APIUser, DID, DIDStatus
from app.schemas import DIDAllocate, DIDCreate, DIDResponse

router = APIRouter()


@router.get("", response_model=List[DIDResponse])
async def list_dids(
    status_filter: str = None,
    tenant_id: str = None,
    db: Session = Depends(get_db),
    api_user: APIUser = Depends(verify_hmac),
):
    """List DIDs with optional filters"""
    query = db.query(DID)

    if status_filter:
        query = query.filter(DID.status == status_filter)
    if tenant_id:
        query = query.filter(DID.tenant_id == tenant_id)

    return query.all()


@router.post("", response_model=DIDResponse, status_code=status.HTTP_201_CREATED)
async def create_did(
    did_data: DIDCreate,
    db: Session = Depends(get_db),
    api_user: APIUser = Depends(verify_hmac),
):
    """Add DID to inventory"""
    # Check if DID already exists
    existing = db.query(DID).filter(DID.e164 == did_data.e164).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="DID already exists",
        )

    did = DID(
        id=uuid4(),
        e164=did_data.e164,
        status=DIDStatus.FREE,
    )
    db.add(did)
    db.commit()
    db.refresh(did)
    return did


@router.post("/allocate")
async def allocate_dids(
    allocation: DIDAllocate,
    db: Session = Depends(get_db),
    api_user: APIUser = Depends(verify_hmac),
):
    """Allocate DIDs to tenant"""
    allocated = []

    for did_number in allocation.dids:
        did = db.query(DID).filter(DID.e164 == did_number).first()

        if not did:
            # Create new DID
            did = DID(
                id=uuid4(),
                e164=did_number,
                tenant_id=allocation.tenant_id,
                status=DIDStatus.ASSIGNED,
            )
            db.add(did)
        elif did.status == DIDStatus.FREE:
            # Assign existing free DID
            did.tenant_id = allocation.tenant_id
            did.status = DIDStatus.ASSIGNED
        else:
            continue  # Skip already assigned DIDs

        allocated.append(did_number)

    db.commit()

    return {
        "tenant_id": str(allocation.tenant_id),
        "allocated": allocated,
        "count": len(allocated),
    }


@router.delete("/{did_id}", status_code=status.HTTP_204_NO_CONTENT)
async def release_did(
    did_id: str,
    db: Session = Depends(get_db),
    api_user: APIUser = Depends(verify_hmac),
):
    """Release DID from tenant"""
    did = db.query(DID).filter(DID.id == did_id).first()
    if not did:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DID not found",
        )

    did.tenant_id = None
    did.status = DIDStatus.FREE
    did.routing_json = {}
    db.commit()
