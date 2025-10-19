"""
Tests for API HMAC authentication
"""
import hashlib
import hmac
import time
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base, get_db
from app.main import app
from app.models import APIUser, APIUserRole


# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(scope="function")
def test_db():
    """Create test database"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def api_user(test_db):
    """Create test API user"""
    db = TestingSessionLocal()
    user = APIUser(
        username="test-user",
        secret_hash="test-secret",
        role=APIUserRole.ADMIN,
        enabled=True,
    )
    db.add(user)
    db.commit()
    db.close()
    return user


def generate_hmac_headers(username: str, secret: str, method: str, path: str, body: bytes = b""):
    """Generate HMAC authentication headers"""
    timestamp = str(int(time.time()))
    body_hash = hashlib.sha256(body).hexdigest()
    message = f"{username}|{method}|{path}|{timestamp}|{body_hash}"
    signature = hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()
    
    return {
        "X-PBX-API-USER": username,
        "X-PBX-TIMESTAMP": timestamp,
        "X-PBX-SIGNATURE": signature,
    }


def test_health_check():
    """Test health check endpoint (no auth required)"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_hmac_auth_valid(api_user):
    """Test valid HMAC authentication"""
    headers = generate_hmac_headers("test-user", "test-secret", "GET", "/auth/test")
    response = client.get("/auth/test", headers=headers)
    assert response.status_code == 200
    assert response.json()["user"] == "test-user"


def test_hmac_auth_invalid_signature(api_user):
    """Test invalid HMAC signature"""
    headers = generate_hmac_headers("test-user", "wrong-secret", "GET", "/auth/test")
    response = client.get("/auth/test", headers=headers)
    assert response.status_code == 401


def test_hmac_auth_expired_timestamp(api_user):
    """Test expired timestamp"""
    old_timestamp = str(int(time.time()) - 400)  # 400 seconds ago
    body_hash = hashlib.sha256(b"").hexdigest()
    message = f"test-user|GET|/auth/test|{old_timestamp}|{body_hash}"
    signature = hmac.new(b"test-secret", message.encode(), hashlib.sha256).hexdigest()
    
    headers = {
        "X-PBX-API-USER": "test-user",
        "X-PBX-TIMESTAMP": old_timestamp,
        "X-PBX-SIGNATURE": signature,
    }
    
    response = client.get("/auth/test", headers=headers)
    assert response.status_code == 401


def test_hmac_auth_missing_user(test_db):
    """Test HMAC with non-existent user"""
    headers = generate_hmac_headers("nonexistent", "secret", "GET", "/auth/test")
    response = client.get("/auth/test", headers=headers)
    assert response.status_code == 401
