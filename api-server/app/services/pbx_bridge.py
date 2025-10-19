"""
PBX Bridge Service - Communicate with PBX core engine
"""
import logging

import requests

from app.settings import settings

logger = logging.getLogger(__name__)


class PBXBridge:
    """Bridge to communicate with PBX core engine"""

    def __init__(self):
        self.pbx_url = settings.PBX_CORE_URL

    def reload_tenant(self, tenant_id: str):
        """Signal PBX core to reload tenant configuration"""
        try:
            url = f"{self.pbx_url}/reload/tenant/{tenant_id}"
            response = requests.post(url, timeout=5)
            if response.status_code == 200:
                logger.info(f"Reloaded tenant {tenant_id} configuration in PBX core")
                return True
            else:
                logger.error(
                    f"Failed to reload tenant {tenant_id}: {response.status_code}"
                )
                return False
        except Exception as e:
            logger.error(f"Error communicating with PBX core: {e}")
            return False

    def reload_routing(self):
        """Signal PBX core to reload routing rules"""
        try:
            url = f"{self.pbx_url}/reload/routing"
            response = requests.post(url, timeout=5)
            if response.status_code == 200:
                logger.info("Reloaded routing configuration in PBX core")
                return True
            else:
                logger.error(f"Failed to reload routing: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error communicating with PBX core: {e}")
            return False

    def reload_ivr(self, tenant_id: str, ivr_id: str):
        """Signal PBX core to reload IVR tree"""
        try:
            url = f"{self.pbx_url}/reload/ivr/{tenant_id}/{ivr_id}"
            response = requests.post(url, timeout=5)
            if response.status_code == 200:
                logger.info(f"Reloaded IVR {ivr_id} in PBX core")
                return True
            else:
                logger.error(f"Failed to reload IVR: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error communicating with PBX core: {e}")
            return False

    def hangup_call(self, call_id: str):
        """Hangup specific call"""
        try:
            url = f"{self.pbx_url}/calls/{call_id}/hangup"
            response = requests.post(url, timeout=5)
            if response.status_code == 200:
                logger.info(f"Hung up call {call_id}")
                return True
            else:
                logger.error(f"Failed to hangup call: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error communicating with PBX core: {e}")
            return False


# Global instance
pbx_bridge = PBXBridge()
