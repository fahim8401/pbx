"""
Extension authentication cache - fetches from API and caches credentials
"""
import hashlib
import logging
import time
from typing import Dict, Optional

import requests

from .config import config

logger = logging.getLogger(__name__)


class AuthStore:
    """Manages extension authentication with API backend"""

    def __init__(self):
        self.cache: Dict[str, Dict] = {}
        self.failed_attempts: Dict[str, int] = {}
        self.lockout: Dict[str, float] = {}

    def authenticate(self, username: str, password: str, realm: str) -> bool:
        """
        Authenticate extension credentials
        Returns True if valid, False otherwise
        """
        # Check if locked out
        if username in self.lockout:
            if time.time() < self.lockout[username]:
                logger.warning(f"Authentication blocked for {username} - locked out")
                return False
            else:
                del self.lockout[username]
                self.failed_attempts[username] = 0

        # Check cache first
        cached = self._get_from_cache(username)
        if cached:
            if self._verify_password(password, cached.get("secret_hash")):
                self.failed_attempts[username] = 0
                return True
            else:
                self._handle_failed_attempt(username)
                return False

        # Fetch from API
        extension = self._fetch_from_api(username)
        if not extension:
            self._handle_failed_attempt(username)
            return False

        # Cache and verify
        self._cache_extension(username, extension)
        if self._verify_password(password, extension.get("secret_hash")):
            self.failed_attempts[username] = 0
            return True
        else:
            self._handle_failed_attempt(username)
            return False

    def _get_from_cache(self, username: str) -> Optional[Dict]:
        """Get extension from cache if not expired"""
        if username in self.cache:
            entry = self.cache[username]
            if time.time() - entry["cached_at"] < config.AUTH_CACHE_TTL:
                return entry["data"]
            else:
                del self.cache[username]
        return None

    def _cache_extension(self, username: str, data: Dict):
        """Cache extension data"""
        self.cache[username] = {"data": data, "cached_at": time.time()}

    def _fetch_from_api(self, username: str) -> Optional[Dict]:
        """Fetch extension from API"""
        try:
            # This would be a real API call in production
            # For now, return stub data
            logger.info(f"Fetching extension {username} from API")
            # url = f"{config.API_URL}/api/v1/extensions/{username}"
            # response = requests.get(url, timeout=5)
            # if response.status_code == 200:
            #     return response.json()
            return None
        except Exception as e:
            logger.error(f"Failed to fetch extension from API: {e}")
            return None

    def _verify_password(self, password: str, secret_hash: str) -> bool:
        """Verify password against hash"""
        # Simple SHA256 hash comparison
        computed_hash = hashlib.sha256(password.encode()).hexdigest()
        return computed_hash == secret_hash

    def _handle_failed_attempt(self, username: str):
        """Handle failed authentication attempt"""
        self.failed_attempts[username] = self.failed_attempts.get(username, 0) + 1

        if self.failed_attempts[username] >= 5:
            # Lockout for 15 minutes
            self.lockout[username] = time.time() + 900
            logger.warning(f"Locked out {username} after {self.failed_attempts[username]} failed attempts")

    def invalidate_cache(self, username: Optional[str] = None):
        """Invalidate cache for specific user or all"""
        if username:
            self.cache.pop(username, None)
        else:
            self.cache.clear()


# Global auth store instance
auth_store = AuthStore()
