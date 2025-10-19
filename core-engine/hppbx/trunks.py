"""
Trunk management - registration, priority, failover
"""
import logging
from typing import Dict, List, Optional

try:
    import pjsua2 as pj
except ImportError:
    pj = None

logger = logging.getLogger(__name__)


class Trunk:
    """Represents a SIP trunk"""

    def __init__(
        self,
        trunk_id: str,
        name: str,
        host: str,
        username: str,
        secret: str,
        priority: int = 100,
        enabled: bool = True,
    ):
        self.trunk_id = trunk_id
        self.name = name
        self.host = host
        self.username = username
        self.secret = secret
        self.priority = priority
        self.enabled = enabled
        self.account = None
        self.registered = False

    def register(self, endpoint):
        """Register trunk with PJSIP"""
        if pj is None:
            logger.warning(f"PJSIP not available - cannot register trunk {self.name}")
            return False

        try:
            acc_cfg = pj.AccountConfig()
            acc_cfg.idUri = f"sip:{self.username}@{self.host}"
            acc_cfg.regConfig.registrarUri = f"sip:{self.host}"

            cred = pj.AuthCredInfo("digest", "*", self.username, 0, self.secret)
            acc_cfg.sipConfig.authCreds.append(cred)

            # Create account
            self.account = pj.Account()
            self.account.create(acc_cfg)

            logger.info(f"Trunk {self.name} registration initiated")
            return True

        except Exception as e:
            logger.error(f"Failed to register trunk {self.name}: {e}")
            return False

    def unregister(self):
        """Unregister trunk"""
        if self.account:
            try:
                self.account.shutdown()
                self.registered = False
                logger.info(f"Trunk {self.name} unregistered")
            except Exception as e:
                logger.error(f"Failed to unregister trunk {self.name}: {e}")


class TrunkManager:
    """Manages all trunks with priority and failover"""

    def __init__(self):
        self.trunks: Dict[str, Trunk] = {}

    def add_trunk(self, trunk: Trunk):
        """Add trunk to manager"""
        self.trunks[trunk.trunk_id] = trunk
        logger.info(f"Added trunk: {trunk.name} (priority: {trunk.priority})")

    def remove_trunk(self, trunk_id: str):
        """Remove trunk"""
        if trunk_id in self.trunks:
            trunk = self.trunks[trunk_id]
            trunk.unregister()
            del self.trunks[trunk_id]
            logger.info(f"Removed trunk: {trunk.name}")

    def get_trunk_by_priority(self, exclude_ids: Optional[List[str]] = None) -> Optional[Trunk]:
        """Get highest priority available trunk"""
        exclude_ids = exclude_ids or []
        available = [
            t
            for t in self.trunks.values()
            if t.enabled and t.trunk_id not in exclude_ids
        ]

        if not available:
            return None

        # Sort by priority (lower number = higher priority)
        available.sort(key=lambda t: t.priority)
        return available[0]

    def register_all(self, endpoint):
        """Register all enabled trunks"""
        for trunk in self.trunks.values():
            if trunk.enabled:
                trunk.register(endpoint)

    def unregister_all(self):
        """Unregister all trunks"""
        for trunk in self.trunks.values():
            trunk.unregister()

    def reload_from_api(self):
        """Reload trunk configuration from API"""
        # Stub - would fetch from API and update trunks
        logger.info("Reloading trunks from API")


# Global trunk manager
trunk_manager = TrunkManager()
