"""
Tests for IVR system
"""
import pytest

from core_engine.hppbx.ivr import IVRNode, IVRSession, IVRTree


def test_ivr_node_creation():
    """Test IVR node creation"""
    node = IVRNode(
        node_id="root",
        name="Main Menu",
        welcome_prompt="welcome.wav",
        invalid_prompt="invalid.wav",
        timeout_seconds=5,
        max_retries=3,
        options={
            "0": {"action": "extension", "value": "101"},
            "1": {"action": "repeat"},
        },
    )
    
    assert node.node_id == "root"
    assert node.get_option("0") == {"action": "extension", "value": "101"}
    assert node.get_option("1") == {"action": "repeat"}
    assert node.get_option("9") is None


def test_ivr_valid_option():
    """Test IVR handling of valid DTMF option"""
    root_node = IVRNode(
        node_id="root",
        name="Main Menu",
        welcome_prompt="welcome.wav",
        options={
            "0": {"action": "extension", "value": "101"},
            "1": {"action": "repeat"},
        },
    )
    
    tree = IVRTree("tree1", "tenant1", "Main Menu", root_node)
    session = IVRSession("session1", "call1", "tenant1", tree, max_depth=5)
    session.start()
    
    # Press 0 - should route to extension
    result = session.handle_dtmf("0")
    assert result["action"] == "transfer"
    assert result["type"] == "extension"
    assert result["value"] == "101"


def test_ivr_invalid_option():
    """Test IVR handling of invalid DTMF option"""
    root_node = IVRNode(
        node_id="root",
        name="Main Menu",
        welcome_prompt="welcome.wav",
        invalid_prompt="invalid.wav",
        max_retries=3,
        options={
            "0": {"action": "extension", "value": "101"},
        },
    )
    
    tree = IVRTree("tree1", "tenant1", "Main Menu", root_node)
    session = IVRSession("session1", "call1", "tenant1", tree)
    session.start()
    
    # Press 9 - invalid option
    result = session.handle_dtmf("9")
    assert result["action"] == "play"
    assert result["file"] == "invalid.wav"


def test_ivr_repeat_option():
    """Test IVR repeat functionality"""
    root_node = IVRNode(
        node_id="root",
        name="Main Menu",
        welcome_prompt="welcome.wav",
        options={
            "1": {"action": "repeat"},
        },
    )
    
    tree = IVRTree("tree1", "tenant1", "Main Menu", root_node)
    session = IVRSession("session1", "call1", "tenant1", tree)
    session.start()
    
    # Press 1 - should replay welcome
    result = session.handle_dtmf("1")
    assert result["action"] == "play"
    assert result["file"] == "welcome.wav"


def test_ivr_max_retries():
    """Test IVR max retries limit"""
    root_node = IVRNode(
        node_id="root",
        name="Main Menu",
        welcome_prompt="welcome.wav",
        invalid_prompt="invalid.wav",
        max_retries=2,
        options={},
    )
    
    tree = IVRTree("tree1", "tenant1", "Main Menu", root_node)
    session = IVRSession("session1", "call1", "tenant1", tree)
    session.start()
    
    # First invalid attempt
    session.handle_dtmf("9")
    # Second invalid attempt
    result = session.handle_dtmf("9")
    
    # Should hangup after max retries
    assert result["action"] == "hangup"
    assert result["reason"] == "max_retries"


def test_ivr_depth_limit():
    """Test IVR depth limit enforcement"""
    root_node = IVRNode(
        node_id="root",
        name="Root",
        welcome_prompt="welcome.wav",
        options={
            "1": {"action": "submenu", "value": "child1"},
        },
    )
    
    tree = IVRTree("tree1", "tenant1", "Main Menu", root_node)
    
    # Create deep nesting
    session = IVRSession("session1", "call1", "tenant1", tree, max_depth=2)
    session.start()
    
    # Manually set depth to limit
    session.current_depth = 2
    
    result = session.handle_dtmf("1")
    assert result["action"] == "hangup"
    assert result["reason"] == "depth_limit"
