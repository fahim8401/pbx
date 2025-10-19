"""
Event system - push call events to API/WebSocket
"""
import logging
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class Event:
    """Represents a PBX event"""

    def __init__(
        self,
        event_type: str,
        call_id: str,
        tenant_id: str,
        data: Optional[Dict] = None,
    ):
        self.event_type = event_type
        self.call_id = call_id
        self.tenant_id = tenant_id
        self.data = data or {}
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        """Convert to dictionary for transmission"""
        return {
            "event_type": self.event_type,
            "call_id": self.call_id,
            "tenant_id": self.tenant_id,
            "data": self.data,
            "timestamp": self.timestamp,
        }


class EventPublisher:
    """Publishes events to API and WebSocket service"""

    def __init__(self):
        self.event_queue = []
        self.api_url = None
        self.websocket_url = None

    def configure(self, api_url: str, websocket_url: Optional[str] = None):
        """Configure event publisher"""
        self.api_url = api_url
        self.websocket_url = websocket_url

    def publish(self, event: Event):
        """Publish event"""
        logger.debug(f"Publishing event: {event.event_type} for call {event.call_id}")

        # Add to queue for batch processing
        self.event_queue.append(event)

        # For critical events, send immediately
        if event.event_type in ["call_started", "call_answered", "call_ended"]:
            self._send_to_api(event)
            self._send_to_websocket(event)

    def _send_to_api(self, event: Event):
        """Send event to API"""
        # Stub - would POST to API
        logger.debug(f"Sending event to API: {event.event_type}")

    def _send_to_websocket(self, event: Event):
        """Send event to WebSocket service for live updates"""
        # Stub - would push to WebSocket
        logger.debug(f"Sending event to WebSocket: {event.event_type}")

    def flush_queue(self):
        """Flush event queue"""
        if self.event_queue:
            logger.info(f"Flushing {len(self.event_queue)} events")
            # Batch send events
            self.event_queue.clear()


# Convenience functions for common events
def publish_call_started(call_id: str, tenant_id: str, src: str, dst: str, direction: str):
    """Publish call started event"""
    event = Event(
        "call_started",
        call_id,
        tenant_id,
        {"src": src, "dst": dst, "direction": direction},
    )
    event_publisher.publish(event)


def publish_call_answered(call_id: str, tenant_id: str):
    """Publish call answered event"""
    event = Event("call_answered", call_id, tenant_id)
    event_publisher.publish(event)


def publish_call_ended(
    call_id: str, tenant_id: str, duration: int, billsec: int, disposition: str
):
    """Publish call ended event"""
    event = Event(
        "call_ended",
        call_id,
        tenant_id,
        {"duration": duration, "billsec": billsec, "disposition": disposition},
    )
    event_publisher.publish(event)


def publish_call_transferred(call_id: str, tenant_id: str, destination: str):
    """Publish call transferred event"""
    event = Event(
        "call_transferred", call_id, tenant_id, {"destination": destination}
    )
    event_publisher.publish(event)


def publish_recording_started(call_id: str, tenant_id: str, path: str):
    """Publish recording started event"""
    event = Event("recording_started", call_id, tenant_id, {"path": path})
    event_publisher.publish(event)


def publish_recording_stopped(
    call_id: str, tenant_id: str, path: str, duration: int, size_bytes: int
):
    """Publish recording stopped event"""
    event = Event(
        "recording_stopped",
        call_id,
        tenant_id,
        {"path": path, "duration": duration, "size_bytes": size_bytes},
    )
    event_publisher.publish(event)


# Global event publisher
event_publisher = EventPublisher()
