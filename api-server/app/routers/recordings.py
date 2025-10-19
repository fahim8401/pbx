"""
Recordings router - Recordings list and presigned URLs
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import verify_hmac
from app.models import APIUser, Recording
from app.schemas import (
    RecordingPresignRequest,
    RecordingPresignResponse,
    RecordingResponse,
)

router = APIRouter()


@router.get("", response_model=List[RecordingResponse])
async def list_recordings(
    tenant_id: str = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=1000),
    db: Session = Depends(get_db),
    api_user: APIUser = Depends(verify_hmac),
):
    """List recordings"""
    query = db.query(Recording)

    if tenant_id:
        query = query.filter(Recording.tenant_id == tenant_id)

    # Pagination
    offset = (page - 1) * size
    query = query.order_by(Recording.created_at.desc()).offset(offset).limit(size)

    return query.all()


@router.post("/presign", response_model=RecordingPresignResponse)
async def presign_recording(
    request: RecordingPresignRequest,
    db: Session = Depends(get_db),
    api_user: APIUser = Depends(verify_hmac),
):
    """Generate presigned URL for recording download"""
    recording = (
        db.query(Recording).filter(Recording.id == request.recording_id).first()
    )

    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found",
        )

    # Generate presigned URL (stub - would use S3/MinIO)
    # In production, use boto3 or minio-py to generate presigned URL
    presigned_url = f"https://storage.hplinkpbx.com/recordings/{recording.path}?token=stub"

    return RecordingPresignResponse(
        url=presigned_url,
        expires_in=3600,  # 1 hour
    )
