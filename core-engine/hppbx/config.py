"""
Configuration loader from environment variables
"""
import os
from typing import Optional


class Config:
    """PBX Core configuration from environment"""

    # PBX Transports
    UDP_PORT: int = int(os.getenv("PBX_UDP_PORT", "5060"))
    TCP_PORT: int = int(os.getenv("PBX_TCP_PORT", "5061"))
    TLS_PORT: int = int(os.getenv("PBX_TLS_PORT", "5062"))
    WSS_PORT: int = int(os.getenv("PBX_WSS_PORT", "5063"))

    # TLS/WSS Certificates
    TLS_CERT_FILE: Optional[str] = os.getenv("PBX_TLS_CERT_FILE")
    TLS_KEY_FILE: Optional[str] = os.getenv("PBX_TLS_KEY_FILE")
    TLS_CA_FILE: Optional[str] = os.getenv("PBX_TLS_CA_FILE")

    # API Connection
    API_URL: str = os.getenv("PBX_API_URL", "http://localhost:8000")
    API_USER: str = os.getenv("PBX_API_USER", "pbx-core")
    API_SECRET: str = os.getenv("PBX_API_SECRET", "changeme")

    # Media Files
    MEDIA_ROOT: str = os.getenv("PBX_MEDIA_ROOT", "/var/lib/hplink-pbx/media")
    RECORDINGS_ROOT: str = os.getenv(
        "PBX_RECORDINGS_ROOT", "/var/lib/hplink-pbx/recordings"
    )

    # RTP Engine (optional)
    RTP_ENGINE_URL: Optional[str] = os.getenv("PBX_RTP_ENGINE_URL")

    # Logging
    LOG_LEVEL: str = os.getenv("PBX_LOG_LEVEL", "INFO")

    # Security
    MAX_CONCURRENT_CALLS_GLOBAL: int = int(
        os.getenv("PBX_MAX_CONCURRENT_CALLS_GLOBAL", "500")
    )
    AUTH_CACHE_TTL: int = int(os.getenv("PBX_AUTH_CACHE_TTL", "300"))
    RATE_LIMIT_PER_IP: int = int(os.getenv("PBX_RATE_LIMIT_PER_IP", "10"))


config = Config()
