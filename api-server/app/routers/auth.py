"""
Authentication router
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import (
    create_access_token,
    create_refresh_token,
    verify_hmac,
    verify_password,
)
from app.models import APIUser, PortalUser
from app.schemas import LoginRequest, TokenResponse

router = APIRouter()


@router.get("/test")
async def test_hmac(api_user: APIUser = Depends(verify_hmac)):
    """Test HMAC authentication"""
    return {
        "status": "ok",
        "message": "HMAC authentication successful",
        "user": api_user.username,
        "role": api_user.role.value,
    }


@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Portal user login"""
    # Find user by email
    user = db.query(PortalUser).filter(PortalUser.email == login_data.email).first()

    if not user or not verify_password(login_data.password, user.pass_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Create tokens
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )
