"""
Security features - rate limiting, concurrency caps, prefix blocking
"""
import logging
import time
from collections import defaultdict
from typing import Dict, List, Set

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiting by IP address"""

    def __init__(self, max_requests_per_minute: int = 60):
        self.max_requests = max_requests_per_minute
        self.requests: Dict[str, List[float]] = defaultdict(list)

    def check_limit(self, ip_address: str) -> bool:
        """
        Check if IP is within rate limit
        Returns True if allowed, False if rate limited
        """
        now = time.time()
        window_start = now - 60  # 1 minute window

        # Clean old requests
        self.requests[ip_address] = [
            req_time
            for req_time in self.requests[ip_address]
            if req_time > window_start
        ]

        # Check limit
        if len(self.requests[ip_address]) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for IP: {ip_address}")
            return False

        # Record request
        self.requests[ip_address].append(now)
        return True


class ConcurrencyLimiter:
    """Track and enforce concurrent call limits"""

    def __init__(self):
        self.tenant_calls: Dict[str, Set[str]] = defaultdict(set)
        self.global_calls: Set[str] = set()

    def add_call(self, call_id: str, tenant_id: str):
        """Add call to tracking"""
        self.global_calls.add(call_id)
        self.tenant_calls[tenant_id].add(call_id)

    def remove_call(self, call_id: str, tenant_id: str):
        """Remove call from tracking"""
        self.global_calls.discard(call_id)
        self.tenant_calls[tenant_id].discard(call_id)

    def check_tenant_limit(self, tenant_id: str, limit: int) -> bool:
        """Check if tenant is under concurrency limit"""
        count = len(self.tenant_calls[tenant_id])
        if count >= limit:
            logger.warning(
                f"Tenant {tenant_id} at concurrency limit: {count}/{limit}"
            )
            return False
        return True

    def check_global_limit(self, limit: int) -> bool:
        """Check global concurrency limit"""
        count = len(self.global_calls)
        if count >= limit:
            logger.warning(f"Global concurrency limit reached: {count}/{limit}")
            return False
        return True

    def get_tenant_count(self, tenant_id: str) -> int:
        """Get active call count for tenant"""
        return len(self.tenant_calls[tenant_id])

    def get_global_count(self) -> int:
        """Get total active call count"""
        return len(self.global_calls)


class PrefixBlocker:
    """Manage allowed and blocked call prefixes"""

    def __init__(self):
        self.tenant_rules: Dict[str, Dict] = {}

    def set_tenant_rules(
        self,
        tenant_id: str,
        allowed_prefixes: List[str],
        blocked_prefixes: List[str],
    ):
        """Set prefix rules for tenant"""
        self.tenant_rules[tenant_id] = {
            "allowed": allowed_prefixes,
            "blocked": blocked_prefixes,
        }

    def is_allowed(self, tenant_id: str, destination: str) -> bool:
        """
        Check if destination is allowed for tenant
        Returns True if allowed, False if blocked
        """
        if tenant_id not in self.tenant_rules:
            # No rules = allow all
            return True

        rules = self.tenant_rules[tenant_id]
        blocked = rules.get("blocked", [])
        allowed = rules.get("allowed", [])

        # Check blocked first
        for prefix in blocked:
            if destination.startswith(prefix):
                logger.warning(
                    f"Blocked prefix {prefix} for tenant {tenant_id}: {destination}"
                )
                return False

        # If allowed list exists, must match
        if allowed:
            for prefix in allowed:
                if destination.startswith(prefix):
                    return True
            logger.warning(
                f"Destination not in allowed list for tenant {tenant_id}: {destination}"
            )
            return False

        # No blocking, no allowed list = allow
        return True


class FraudDetector:
    """Detect suspicious calling patterns"""

    def __init__(self):
        self.daily_spend: Dict[str, float] = defaultdict(float)
        self.daily_limits: Dict[str, float] = {}

    def set_daily_limit(self, tenant_id: str, limit: float):
        """Set daily spend limit for tenant"""
        self.daily_limits[tenant_id] = limit

    def add_charge(self, tenant_id: str, amount: float) -> bool:
        """
        Add charge to daily spend
        Returns True if under limit, False if limit exceeded
        """
        self.daily_spend[tenant_id] += amount

        if tenant_id in self.daily_limits:
            limit = self.daily_limits[tenant_id]
            if self.daily_spend[tenant_id] >= limit:
                logger.warning(
                    f"Daily spend limit exceeded for tenant {tenant_id}: "
                    f"{self.daily_spend[tenant_id]:.2f}/{limit:.2f}"
                )
                return False

        return True

    def reset_daily_spend(self):
        """Reset daily spend counters (called by daily cron)"""
        self.daily_spend.clear()
        logger.info("Daily spend counters reset")


# Global security instances
rate_limiter = RateLimiter()
concurrency_limiter = ConcurrencyLimiter()
prefix_blocker = PrefixBlocker()
fraud_detector = FraudDetector()
