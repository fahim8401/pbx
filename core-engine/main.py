"""
HPLink PBX Core - Main entry point
"""
import logging
import signal
import sys
import time

from hppbx.auth_store import auth_store
from hppbx.calls import call_manager
from hppbx.config import config
from hppbx.engine import engine
from hppbx.events import event_publisher
from hppbx.ivr import ivr_manager
from hppbx.routing import router
from hppbx.rtp import RTPEngineClient, rtpengine
from hppbx.security import (
    concurrency_limiter,
    fraud_detector,
    prefix_blocker,
    rate_limiter,
)
from hppbx.trunks import trunk_manager

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


class PBXApplication:
    """Main PBX application"""

    def __init__(self):
        self.running = False

    def start(self):
        """Start PBX core"""
        logger.info("Starting HPLink PBX Core...")

        try:
            # Initialize engine
            engine.initialize()

            # Configure event publisher
            event_publisher.configure(
                api_url=config.API_URL,
                websocket_url=None,  # Optional WebSocket service
            )

            # Initialize RTPEngine if configured
            if config.RTP_ENGINE_URL:
                global rtpengine
                rtpengine = RTPEngineClient(config.RTP_ENGINE_URL)
                logger.info(f"RTPEngine configured: {config.RTP_ENGINE_URL}")

            # Register signal handlers
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)

            self.running = True
            logger.info("HPLink PBX Core started successfully")
            logger.info(f"UDP port: {config.UDP_PORT}")
            logger.info(f"TCP port: {config.TCP_PORT}")
            logger.info(f"TLS port: {config.TLS_PORT}")
            logger.info(f"WSS port: {config.WSS_PORT}")

            # Main loop
            self._main_loop()

        except Exception as e:
            logger.error(f"Failed to start PBX core: {e}", exc_info=True)
            sys.exit(1)

    def _main_loop(self):
        """Main application loop"""
        logger.info("Entering main loop...")

        while self.running:
            try:
                # Periodic tasks
                time.sleep(1)

                # Flush event queue periodically
                if int(time.time()) % 10 == 0:
                    event_publisher.flush_queue()

            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown()

    def shutdown(self):
        """Shutdown PBX core"""
        logger.info("Shutting down HPLink PBX Core...")
        self.running = False

        # Hangup all calls
        engine.hangup_all()

        # Unregister trunks
        trunk_manager.unregister_all()

        # Shutdown engine
        engine.shutdown()

        logger.info("HPLink PBX Core shutdown complete")
        sys.exit(0)


def main():
    """Entry point"""
    app = PBXApplication()
    app.start()


if __name__ == "__main__":
    main()
