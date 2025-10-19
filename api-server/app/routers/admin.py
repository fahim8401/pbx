"""
Admin router - Admin-specific endpoints
"""
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import verify_hmac
from app.models import APIUser

router = APIRouter()


@router.get("/active-calls")
async def get_active_calls(
    db: Session = Depends(get_db),
    api_user: APIUser = Depends(verify_hmac),
):
    """Get active calls (stub - would query from PBX core or WebSocket service)"""
    # In production, this would query the PBX core engine or a Redis cache
    return {
        "active_calls": [],
        "total_count": 0,
    }


@router.get("/fraud-rules")
async def get_fraud_rules(
    db: Session = Depends(get_db),
    api_user: APIUser = Depends(verify_hmac),
):
    """Get fraud detection rules (stub)"""
    return {
        "rules": [],
    }
