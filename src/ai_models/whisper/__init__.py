"""
Whisper speech recognition module for voice-based trading commands and analysis.
"""

from .whisper_client import WhisperClient, WhisperConfig, WhisperResponse

__all__ = [
    'WhisperClient',
    'WhisperConfig',
    'WhisperResponse'
]