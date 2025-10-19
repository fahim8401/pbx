"""
IVR (Interactive Voice Response) system
Handles DTMF input, timeouts, invalid options, and nested menus
"""
import logging
import time
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class IVRNode:
    """Represents a single IVR menu node"""

    def __init__(
        self,
        node_id: str,
        name: str,
        welcome_prompt: str,
        invalid_prompt: str = "invalid.wav",
        timeout_seconds: int = 5,
        max_retries: int = 3,
        options: Optional[Dict[str, Dict]] = None,
    ):
        self.node_id = node_id
        self.name = name
        self.welcome_prompt = welcome_prompt
        self.invalid_prompt = invalid_prompt
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.options = options or {}
        # Options format: {"1": {"action": "extension", "value": "101"}}

    def get_option(self, digit: str) -> Optional[Dict]:
        """Get action for DTMF digit"""
        return self.options.get(digit)


class IVRSession:
    """Represents an active IVR session"""

    def __init__(
        self,
        session_id: str,
        call_id: str,
        tenant_id: str,
        ivr_tree: "IVRTree",
        max_depth: int = 5,
    ):
        self.session_id = session_id
        self.call_id = call_id
        self.tenant_id = tenant_id
        self.ivr_tree = ivr_tree
        self.max_depth = max_depth
        self.current_depth = 0
        self.current_node: Optional[IVRNode] = None
        self.retry_count = 0
        self.started_at = time.time()

    def start(self):
        """Start IVR session at root node"""
        self.current_node = self.ivr_tree.root_node
        self.current_depth = 0
        logger.info(f"IVR session {self.session_id} started")
        return self._play_welcome()

    def handle_dtmf(self, digit: str) -> Dict:
        """
        Handle DTMF input
        Returns action to take
        """
        if not self.current_node:
            return {"action": "error", "reason": "No active node"}

        # Check depth limit
        if self.current_depth >= self.max_depth:
            logger.warning(f"IVR depth limit reached: {self.current_depth}")
            return {"action": "hangup", "reason": "depth_limit"}

        option = self.current_node.get_option(digit)

        if not option:
            # Invalid option
            self.retry_count += 1
            if self.retry_count >= self.current_node.max_retries:
                logger.warning(f"Max retries reached in IVR {self.session_id}")
                return {"action": "hangup", "reason": "max_retries"}

            logger.info(f"Invalid IVR option: {digit}")
            return {
                "action": "play",
                "file": self.current_node.invalid_prompt,
                "then": "replay_welcome",
            }

        # Valid option - reset retry count
        self.retry_count = 0

        # Handle different action types
        action_type = option.get("action")

        if action_type == "repeat":
            return self._play_welcome()

        elif action_type == "extension":
            return {
                "action": "transfer",
                "type": "extension",
                "value": option.get("value"),
            }

        elif action_type == "queue":
            return {
                "action": "transfer",
                "type": "queue",
                "value": option.get("value"),
            }

        elif action_type == "ring_group":
            return {
                "action": "transfer",
                "type": "ring_group",
                "value": option.get("value"),
            }

        elif action_type == "submenu":
            # Navigate to child menu
            child_node_id = option.get("value")
            child_node = self.ivr_tree.get_node(child_node_id)
            if child_node:
                self.current_node = child_node
                self.current_depth += 1
                return self._play_welcome()
            else:
                logger.error(f"Child IVR node not found: {child_node_id}")
                return {"action": "hangup", "reason": "invalid_submenu"}

        elif action_type == "voicemail":
            return {"action": "voicemail", "value": option.get("value")}

        else:
            logger.error(f"Unknown IVR action type: {action_type}")
            return {"action": "hangup", "reason": "invalid_action"}

    def handle_timeout(self) -> Dict:
        """Handle input timeout"""
        self.retry_count += 1
        if self.retry_count >= (self.current_node.max_retries if self.current_node else 3):
            return {"action": "hangup", "reason": "timeout"}

        logger.info(f"IVR timeout in session {self.session_id}")
        return self._play_welcome()

    def _play_welcome(self) -> Dict:
        """Play welcome prompt"""
        if self.current_node:
            return {
                "action": "play",
                "file": self.current_node.welcome_prompt,
                "then": "wait_dtmf",
            }
        return {"action": "error"}


class IVRTree:
    """Represents a complete IVR tree"""

    def __init__(self, tree_id: str, tenant_id: str, name: str, root_node: IVRNode):
        self.tree_id = tree_id
        self.tenant_id = tenant_id
        self.name = name
        self.root_node = root_node
        self.nodes: Dict[str, IVRNode] = {root_node.node_id: root_node}

    def add_node(self, node: IVRNode):
        """Add node to tree"""
        self.nodes[node.node_id] = node

    def get_node(self, node_id: str) -> Optional[IVRNode]:
        """Get node by ID"""
        return self.nodes.get(node_id)


class IVRManager:
    """Manages IVR trees and sessions"""

    def __init__(self):
        self.trees: Dict[str, IVRTree] = {}
        self.active_sessions: Dict[str, IVRSession] = {}

    def load_tree(self, tree_data: Dict) -> IVRTree:
        """Load IVR tree from JSON data"""
        # Simplified loader - would parse full tree structure
        tree_id = tree_data.get("tree_id")
        tenant_id = tree_data.get("tenant_id")
        name = tree_data.get("name")

        # Create root node
        root_data = tree_data.get("root", {})
        root_node = IVRNode(
            node_id="root",
            name="Main Menu",
            welcome_prompt=root_data.get("welcome_prompt", "welcome.wav"),
            invalid_prompt=root_data.get("invalid_prompt", "invalid.wav"),
            timeout_seconds=root_data.get("timeout_seconds", 5),
            max_retries=root_data.get("max_retries", 3),
            options=root_data.get("options", {}),
        )

        tree = IVRTree(tree_id, tenant_id, name, root_node)

        # Load child nodes
        for child_data in tree_data.get("children", []):
            child_node = IVRNode(
                node_id=child_data.get("node_id"),
                name=child_data.get("name"),
                welcome_prompt=child_data.get("welcome_prompt"),
                invalid_prompt=child_data.get("invalid_prompt", "invalid.wav"),
                timeout_seconds=child_data.get("timeout_seconds", 5),
                max_retries=child_data.get("max_retries", 3),
                options=child_data.get("options", {}),
            )
            tree.add_node(child_node)

        self.trees[tree_id] = tree
        logger.info(f"Loaded IVR tree: {name} ({tree_id})")
        return tree

    def start_session(
        self, call_id: str, tenant_id: str, tree_id: str, max_depth: int = 5
    ) -> Optional[IVRSession]:
        """Start new IVR session"""
        tree = self.trees.get(tree_id)
        if not tree:
            logger.error(f"IVR tree not found: {tree_id}")
            return None

        session_id = f"ivr_{call_id}"
        session = IVRSession(session_id, call_id, tenant_id, tree, max_depth)
        self.active_sessions[session_id] = session
        session.start()
        return session

    def end_session(self, session_id: str):
        """End IVR session"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            logger.info(f"IVR session {session_id} ended")


# Global IVR manager
ivr_manager = IVRManager()
