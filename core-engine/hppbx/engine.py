"""
PBX Core Engine - PJSIP Endpoint initialization and transport management
"""
import logging
from typing import Optional

try:
    import pjsua2 as pj
except ImportError:
    pj = None
    logging.warning("pjsua2 not available - using stub mode")

from .config import config

logger = logging.getLogger(__name__)


class PBXEngine:
    """Main PBX Engine using PJSIP"""

    def __init__(self):
        self.ep: Optional[pj.Endpoint] = None
        self.transports = {}
        self.accounts = {}

    def initialize(self):
        """Initialize PJSIP endpoint and transports"""
        if pj is None:
            logger.warning("PJSIP not available - running in stub mode")
            return

        try:
            # Create endpoint
            self.ep = pj.Endpoint()
            self.ep.libCreate()

            # Initialize endpoint
            ep_cfg = pj.EpConfig()
            ep_cfg.logConfig.level = 4
            ep_cfg.logConfig.consoleLevel = 4

            self.ep.libInit(ep_cfg)

            # Create transports
            self._create_transports()

            # Start endpoint
            self.ep.libStart()

            logger.info("PBX Engine initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize PBX engine: {e}")
            raise

    def _create_transports(self):
        """Create UDP, TCP, TLS and WSS transports"""
        if not self.ep:
            return

        # UDP Transport
        try:
            udp_cfg = pj.TransportConfig()
            udp_cfg.port = config.UDP_PORT
            udp_transport = self.ep.transportCreate(pj.PJSIP_TRANSPORT_UDP, udp_cfg)
            self.transports["udp"] = udp_transport
            logger.info(f"UDP transport created on port {config.UDP_PORT}")
        except Exception as e:
            logger.error(f"Failed to create UDP transport: {e}")

        # TCP Transport
        try:
            tcp_cfg = pj.TransportConfig()
            tcp_cfg.port = config.TCP_PORT
            tcp_transport = self.ep.transportCreate(pj.PJSIP_TRANSPORT_TCP, tcp_cfg)
            self.transports["tcp"] = tcp_transport
            logger.info(f"TCP transport created on port {config.TCP_PORT}")
        except Exception as e:
            logger.error(f"Failed to create TCP transport: {e}")

        # TLS Transport
        if config.TLS_CERT_FILE and config.TLS_KEY_FILE:
            try:
                tls_cfg = pj.TransportConfig()
                tls_cfg.port = config.TLS_PORT
                tls_cfg.tlsConfig.certFile = config.TLS_CERT_FILE
                tls_cfg.tlsConfig.privKeyFile = config.TLS_KEY_FILE
                if config.TLS_CA_FILE:
                    tls_cfg.tlsConfig.caListFile = config.TLS_CA_FILE
                tls_transport = self.ep.transportCreate(pj.PJSIP_TRANSPORT_TLS, tls_cfg)
                self.transports["tls"] = tls_transport
                logger.info(f"TLS transport created on port {config.TLS_PORT}")
            except Exception as e:
                logger.error(f"Failed to create TLS transport: {e}")

        # WSS Transport (WebRTC)
        if config.TLS_CERT_FILE and config.TLS_KEY_FILE:
            try:
                wss_cfg = pj.TransportConfig()
                wss_cfg.port = config.WSS_PORT
                wss_cfg.tlsConfig.certFile = config.TLS_CERT_FILE
                wss_cfg.tlsConfig.privKeyFile = config.TLS_KEY_FILE
                if config.TLS_CA_FILE:
                    wss_cfg.tlsConfig.caListFile = config.TLS_CA_FILE
                # Note: Actual WSS support requires additional PJSIP configuration
                # This is a simplified version
                logger.info(f"WSS transport configured on port {config.WSS_PORT}")
            except Exception as e:
                logger.error(f"Failed to create WSS transport: {e}")

    def shutdown(self):
        """Shutdown PBX engine"""
        if self.ep:
            try:
                self.ep.libDestroy()
                logger.info("PBX Engine shutdown complete")
            except Exception as e:
                logger.error(f"Error during shutdown: {e}")

    def hangup_all(self):
        """Hangup all active calls"""
        if self.ep:
            try:
                self.ep.hangupAllCalls()
                logger.info("All calls terminated")
            except Exception as e:
                logger.error(f"Error hanging up calls: {e}")


# Global engine instance
engine = PBXEngine()
