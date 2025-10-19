"""
Dependencies - HMAC authentication, JWT utilities, and DB dependencies
"""
import hashlib
import hmac
import time
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import APIUser, PortalUser
from app.settings import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Bearer token scheme
security = HTTPBearer()


# HMAC Authentication
def verify_hmac_signature(
    username: str,
    timestamp: str,
    signature: str,
    method: str,
    path: str,
    body: bytes,
    db: Session,
) -> bool:
    """
    Verify HMAC signature
    Format: HMAC-SHA256(SECRET, USER|METHOD|PATH|TIMESTAMP|SHA256(body))
    """
    # Check timestamp (prevent replay attacks)
    try:
        request_time = int(timestamp)
        current_time = int(time.time())
        if abs(current_time - request_time) > settings.HMAC_CLOCK_SKEW_SECONDS:
            return False
    except ValueError:
        return False

    # Get API user secret
    api_user = db.query(APIUser).filter(
        APIUser.username == username,
        APIUser.enabled == True,
    ).first()

    if not api_user:
        return False

    # Compute expected signature
    body_hash = hashlib.sha256(body).hexdigest()
    message = f"{username}|{method}|{path}|{timestamp}|{body_hash}"

    # Hash the secret (assuming it's stored hashed)
    # In production, you'd fetch the plain secret or use a different approach
    expected_signature = hmac.new(
        api_user.secret_hash.encode(),
        message.encode(),
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(signature, expected_signature)


async def verify_hmac(
    request: Request,
    x_pbx_api_user: str = Header(...),
    x_pbx_timestamp: str = Header(...),
    x_pbx_signature: str = Header(...),
    db: Session = Depends(get_db),
) -> APIUser:
    """HMAC authentication dependency"""
    # Get request body
    body = await request.body()

    # Verify signature
    if not verify_hmac_signature(
        x_pbx_api_user,
        x_pbx_timestamp,
        x_pbx_signature,
        request.method,
        request.url.path,
        body,
        db,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid HMAC signature",
        )

    # Get API user
    api_user = db.query(APIUser).filter(
        APIUser.username == x_pbx_api_user,
        APIUser.enabled == True,
    ).first()

    if not api_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API user not found",
        )

    return api_user


# JWT Authentication
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> dict:
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> PortalUser:
    """Get current authenticated portal user from JWT"""
    token = credentials.credentials
    payload = verify_token(token)

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    user = db.query(PortalUser).filter(PortalUser.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


async def get_current_superadmin(
    current_user: PortalUser = Depends(get_current_user),
) -> PortalUser:
    """Verify current user is superadmin"""
    from app.models import UserRole

    if current_user.role != UserRole.SUPERADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return current_user


# Password utilities
def hash_password(password: str) -> str:
    """Hash password"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password"""
    return pwd_context.verify(plain_password, hashed_password)


def generate_random_password(length: int = 16) -> str:
    """Generate random password"""
    import secrets
    import string

    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()"
    return "".join(secrets.choice(alphabet) for _ in range(length))
