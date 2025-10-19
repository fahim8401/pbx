"""
Usage router - Usage metrics and CDR
"""
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import verify_hmac
from app.models import APIUser, CDR
from app.schemas import CDRResponse, UsageMetricsRequest, UsageMetricsResponse

router = APIRouter()


@router.get("/metrics", response_model=UsageMetricsResponse)
async def get_usage_metrics(
    tenant_id: str,
    from_date: datetime = Query(...),
    to_date: datetime = Query(...),
    db: Session = Depends(get_db),
    api_user: APIUser = Depends(verify_hmac),
):
    """Get usage metrics for tenant"""
    # Calculate minutes from CDR
    result = (
        db.query(
            func.sum(CDR.billsec).label("total_seconds"),
        )
        .filter(
            CDR.tenant_id == tenant_id,
            CDR.started_at >= from_date,
            CDR.started_at <= to_date,
        )
        .first()
    )

    total_seconds = result.total_seconds or 0
    total_minutes = int(total_seconds / 60)

    # Split by direction (stub - would need direction field in CDR)
    minutes_out = total_minutes // 2  # Simplified
    minutes_in = total_minutes - minutes_out

    # Get storage (stub - would calculate from recordings)
    storage_gb = 0.0

    return UsageMetricsResponse(
        tenant_id=tenant_id,
        from_date=from_date,
        to_date=to_date,
        minutes_in=minutes_in,
        minutes_out=minutes_out,
        storage_gb=storage_gb,
        sms_count=0,
    )


@router.get("/cdr", response_model=List[CDRResponse])
async def get_cdr(
    tenant_id: str = Query(None),
    from_date: datetime = Query(None),
    to_date: datetime = Query(None),
    disposition: str = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=1000),
    db: Session = Depends(get_db),
    api_user: APIUser = Depends(verify_hmac),
):
    """Get CDR records with filters"""
    query = db.query(CDR)

    if tenant_id:
        query = query.filter(CDR.tenant_id == tenant_id)
    if from_date:
        query = query.filter(CDR.started_at >= from_date)
    if to_date:
        query = query.filter(CDR.started_at <= to_date)
    if disposition:
        query = query.filter(CDR.disposition == disposition)

    # Pagination
    offset = (page - 1) * size
    query = query.order_by(CDR.started_at.desc()).offset(offset).limit(size)

    return query.all()
