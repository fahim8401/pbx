"""
Media handling - playback, MOH (Music on Hold), recording
"""
import logging
import os
from typing import Optional

from .config import config

logger = logging.getLogger(__name__)


class MediaPlayer:
    """Handles media file playback"""

    def __init__(self):
        self.media_root = config.MEDIA_ROOT

    def play_file(self, call_id: str, filename: str, loop: bool = False):
        """
        Play media file to call
        Filename is relative to media root
        """
        filepath = os.path.join(self.media_root, filename)

        if not os.path.exists(filepath):
            logger.error(f"Media file not found: {filepath}")
            return False

        logger.info(f"Playing {filename} to call {call_id} (loop={loop})")
        # Stub - would use PJSIP media player
        return True

    def stop_playback(self, call_id: str):
        """Stop media playback on call"""
        logger.info(f"Stopping playback on call {call_id}")
        # Stub
        return True


class MOHPlayer:
    """Music on Hold player"""

    def __init__(self):
        self.moh_file = "moh.wav"
        self.active_holds = {}

    def start_hold(self, call_id: str):
        """Start MOH for held call"""
        logger.info(f"Starting MOH for call {call_id}")
        self.active_holds[call_id] = True
        # Stub - would play moh.wav in loop
        return True

    def stop_hold(self, call_id: str):
        """Stop MOH when call resumes"""
        if call_id in self.active_holds:
            del self.active_holds[call_id]
            logger.info(f"Stopped MOH for call {call_id}")
        return True


class CallRecorder:
    """Handles call recording"""

    def __init__(self):
        self.recordings_root = config.RECORDINGS_ROOT
        self.active_recordings = {}

    def start_recording(
        self, call_id: str, tenant_id: str, recording_policy: str = "all"
    ):
        """
        Start recording call
        Policy: none, external (outbound only), all
        """
        if recording_policy == "none":
            return False

        # Generate recording path
        from datetime import datetime

        date_str = datetime.now().strftime("%Y-%m-%d")
        recording_dir = os.path.join(
            self.recordings_root, tenant_id, date_str
        )

        # Create directory if not exists
        os.makedirs(recording_dir, exist_ok=True)

        recording_path = os.path.join(recording_dir, f"{call_id}.wav")

        logger.info(f"Starting recording for call {call_id}: {recording_path}")
        self.active_recordings[call_id] = {
            "path": recording_path,
            "started_at": datetime.now().timestamp(),
        }

        # Stub - would start PJSIP recorder
        return True

    def stop_recording(self, call_id: str) -> Optional[dict]:
        """
        Stop recording and return metadata
        """
        if call_id not in self.active_recordings:
            return None

        recording = self.active_recordings[call_id]
        del self.active_recordings[call_id]

        from datetime import datetime

        duration = datetime.now().timestamp() - recording["started_at"]

        metadata = {
            "call_id": call_id,
            "path": recording["path"],
            "duration": int(duration),
            "size_bytes": 0,  # Would get actual file size
        }

        logger.info(f"Stopped recording for call {call_id}")
        # Stub - would send metadata to API
        return metadata


class VoicemailRecorder:
    """Handles voicemail recording"""

    def __init__(self):
        self.voicemail_root = os.path.join(config.MEDIA_ROOT, "voicemail")

    def record_voicemail(self, extension: str, call_id: str):
        """Record voicemail message"""
        from datetime import datetime

        voicemail_dir = os.path.join(self.voicemail_root, extension)
        os.makedirs(voicemail_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        voicemail_path = os.path.join(voicemail_dir, f"{timestamp}_{call_id}.wav")

        logger.info(f"Recording voicemail for {extension}: {voicemail_path}")
        # Stub - would record voicemail and send notification
        return voicemail_path


# Global instances
media_player = MediaPlayer()
moh_player = MOHPlayer()
call_recorder = CallRecorder()
voicemail_recorder = VoicemailRecorder()
