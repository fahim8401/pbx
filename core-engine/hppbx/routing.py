"""
Call routing - inbound DID to target, outbound prefix to trunk
"""
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class RoutingRule:
    """Represents a routing rule"""

    def __init__(
        self,
        rule_id: str,
        pattern: str,
        target_type: str,
        target_value: str,
        tenant_id: Optional[str] = None,
    ):
        self.rule_id = rule_id
        self.pattern = pattern  # DID or prefix pattern
        self.target_type = target_type  # extension, ivr, queue, ring_group
        self.target_value = target_value
        self.tenant_id = tenant_id


class Router:
    """Handles call routing logic"""

    def __init__(self):
        self.inbound_routes: Dict[str, RoutingRule] = {}
        self.outbound_routes: Dict[str, RoutingRule] = {}

    def add_inbound_route(self, did: str, rule: RoutingRule):
        """Add inbound DID routing"""
        self.inbound_routes[did] = rule
        logger.info(f"Added inbound route: {did} -> {rule.target_type}:{rule.target_value}")

    def add_outbound_route(self, prefix: str, rule: RoutingRule):
        """Add outbound prefix routing"""
        self.outbound_routes[prefix] = rule
        logger.info(f"Added outbound route: {prefix} -> trunk")

    def route_inbound(self, did: str) -> Optional[RoutingRule]:
        """Route inbound call based on DID"""
        # Exact match first
        if did in self.inbound_routes:
            return self.inbound_routes[did]

        # Pattern matching (simplified)
        for pattern, rule in self.inbound_routes.items():
            if self._pattern_match(did, pattern):
                return rule

        logger.warning(f"No route found for DID: {did}")
        return None

    def route_outbound(self, destination: str, tenant_id: str) -> Optional[Dict]:
        """
        Route outbound call based on destination prefix
        Returns trunk selection and validation result
        """
        # Check tenant permissions
        if not self._check_tenant_permissions(tenant_id, destination):
            logger.warning(f"Tenant {tenant_id} not allowed to call {destination}")
            return None

        # Find matching prefix
        prefix = self._find_longest_prefix(destination)
        if prefix and prefix in self.outbound_routes:
            rule = self.outbound_routes[prefix]
            return {"trunk_id": rule.target_value, "prefix": prefix}

        logger.warning(f"No outbound route for destination: {destination}")
        return None

    def _pattern_match(self, number: str, pattern: str) -> bool:
        """Simple pattern matching (supports * wildcard)"""
        if "*" in pattern:
            prefix = pattern.replace("*", "")
            return number.startswith(prefix)
        return number == pattern

    def _find_longest_prefix(self, destination: str) -> Optional[str]:
        """Find longest matching prefix"""
        matches = [
            prefix
            for prefix in self.outbound_routes.keys()
            if destination.startswith(prefix)
        ]
        if matches:
            return max(matches, key=len)
        return None

    def _check_tenant_permissions(self, tenant_id: str, destination: str) -> bool:
        """Check if tenant is allowed to call destination"""
        # Stub - would check against plan template rules
        # - call_direction (inbound/outbound/both)
        # - allowed_prefixes
        # - blocked_prefixes
        return True

    def reload_from_api(self):
        """Reload routing rules from API"""
        logger.info("Reloading routing rules from API")
        # Stub - would fetch from API


# Global router instance
router = Router()
