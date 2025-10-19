"""
Rating Service - Calculate call costs (stub)
"""
import logging

logger = logging.getLogger(__name__)


class RatingService:
    """Simple rating service for call cost calculation"""

    def __init__(self):
        # Rate tables (stub - would load from database)
        self.default_rate_per_minute = 0.02  # $0.02 per minute

    def calculate_cost(
        self, destination: str, duration_seconds: int, tenant_id: str = None
    ) -> float:
        """
        Calculate call cost
        Returns cost in USD
        """
        # Simple calculation: duration * rate
        minutes = duration_seconds / 60.0
        cost = minutes * self.default_rate_per_minute

        logger.debug(
            f"Calculated cost for {duration_seconds}s to {destination}: ${cost:.4f}"
        )
        return round(cost, 4)

    def get_rate(self, destination: str, tenant_id: str = None) -> float:
        """Get rate per minute for destination"""
        # Stub - would look up in rate table
        return self.default_rate_per_minute


# Global instance
rating_service = RatingService()
