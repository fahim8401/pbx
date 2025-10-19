"""
Call lifecycle management - bridge, transfer, hold
"""
import logging
import time
from typing import Dict, Optional
from uuid import uuid4

try:
    import pjsua2 as pj
except ImportError:
    pj = None

logger = logging.getLogger(__name__)


class Call:
    """Represents an active call"""

    def __init__(
        self,
        call_id: str,
        tenant_id: str,
        src: str,
        dst: str,
        direction: str,
    ):
        self.call_id = call_id
        self.tenant_id = tenant_id
        self.src = src
        self.dst = dst
        self.direction = direction  # inbound, outbound
        self.started_at = time.time()
        self.answered_at: Optional[float] = None
        self.ended_at: Optional[float] = None
        self.disposition = "UNKNOWN"
        self.trunk_id: Optional[str] = None
        self.pjsua_call = None

    def answer(self):
        """Mark call as answered"""
        self.answered_at = time.time()
        self.disposition = "ANSWERED"
        logger.info(f"Call {self.call_id} answered")

    def hangup(self, reason: str = "NORMAL"):
        """Hangup call"""
        self.ended_at = time.time()
        if self.disposition == "ANSWERED":
            self.disposition = reason
        else:
            self.disposition = "NO_ANSWER" if self.answered_at is None else reason

        if self.pjsua_call and pj:
            try:
                self.pjsua_call.hangup(pj.CallOpParam())
            except Exception as e:
                logger.error(f"Error hanging up PJSUA call: {e}")

        logger.info(f"Call {self.call_id} ended: {self.disposition}")

    def get_duration(self) -> int:
        """Get call duration in seconds"""
        if self.ended_at:
            return int(self.ended_at - self.started_at)
        return int(time.time() - self.started_at)

    def get_billsec(self) -> int:
        """Get billable seconds (from answer to hangup)"""
        if self.answered_at and self.ended_at:
            return int(self.ended_at - self.answered_at)
        elif self.answered_at:
            return int(time.time() - self.answered_at)
        return 0


class CallManager:
    """Manages active calls"""

    def __init__(self):
        self.active_calls: Dict[str, Call] = {}
        self.call_history: Dict[str, Call] = {}

    def create_call(
        self, tenant_id: str, src: str, dst: str, direction: str
    ) -> Call:
        """Create new call"""
        call_id = str(uuid4())
        call = Call(call_id, tenant_id, src, dst, direction)
        self.active_calls[call_id] = call
        logger.info(f"Created call {call_id}: {src} -> {dst} ({direction})")
        return call

    def get_call(self, call_id: str) -> Optional[Call]:
        """Get active call by ID"""
        return self.active_calls.get(call_id)

    def end_call(self, call_id: str, reason: str = "NORMAL"):
        """End call and move to history"""
        if call_id in self.active_calls:
            call = self.active_calls[call_id]
            call.hangup(reason)
            self.call_history[call_id] = call
            del self.active_calls[call_id]

            # Send CDR to API
            self._send_cdr(call)

    def get_active_calls_count(self, tenant_id: Optional[str] = None) -> int:
        """Get count of active calls, optionally filtered by tenant"""
        if tenant_id:
            return len([c for c in self.active_calls.values() if c.tenant_id == tenant_id])
        return len(self.active_calls)

    def check_concurrency_limit(self, tenant_id: str, limit: int) -> bool:
        """Check if tenant is under concurrency limit"""
        count = self.get_active_calls_count(tenant_id)
        return count < limit

    def transfer_call(self, call_id: str, destination: str, blind: bool = True):
        """Transfer call to destination"""
        call = self.get_call(call_id)
        if not call:
            logger.error(f"Call {call_id} not found for transfer")
            return False

        # Stub - would implement actual transfer logic
        logger.info(f"Transferring call {call_id} to {destination} (blind={blind})")
        return True

    def hold_call(self, call_id: str):
        """Put call on hold"""
        call = self.get_call(call_id)
        if call and call.pjsua_call and pj:
            try:
                hold_param = pj.CallOpParam()
                call.pjsua_call.setHold(hold_param)
                logger.info(f"Call {call_id} on hold")
                return True
            except Exception as e:
                logger.error(f"Failed to hold call: {e}")
        return False

    def unhold_call(self, call_id: str):
        """Resume call from hold"""
        call = self.get_call(call_id)
        if call and call.pjsua_call and pj:
            try:
                reinvite_param = pj.CallOpParam()
                call.pjsua_call.reinvite(reinvite_param)
                logger.info(f"Call {call_id} resumed from hold")
                return True
            except Exception as e:
                logger.error(f"Failed to unhold call: {e}")
        return False

    def _send_cdr(self, call: Call):
        """Send CDR to API"""
        cdr_data = {
            "call_id": call.call_id,
            "tenant_id": call.tenant_id,
            "src": call.src,
            "dst": call.dst,
            "started_at": call.started_at,
            "ended_at": call.ended_at,
            "billsec": call.get_billsec(),
            "disposition": call.disposition,
            "trunk_id": call.trunk_id,
        }
        logger.info(f"Sending CDR for call {call.call_id}")
        # Stub - would POST to API


# Global call manager
call_manager = CallManager()
