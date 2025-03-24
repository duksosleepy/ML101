"""
Module chứa các thành phần thu âm từ microphone.
"""

# Import các lớp cơ sở trước để các lớp con có thể kế thừa
from .base import BaseAudioInput

# Import factory functions
from .factory import (
    create_audio_input,
    get_available_engines,
    get_or_create_audio_input,
)

# Import các audio input cụ thể
# Các audio input này sẽ tự động đăng ký với Registry
from .pyaudio_input import PYAUDIO_AVAILABLE, PyAudioInput
from .registry import AudioInputRegistry
from .sr_input import SR_AVAILABLE, SpeechRecognitionInput

__all__ = [
    "PYAUDIO_AVAILABLE",
    "SR_AVAILABLE",
    "AudioInputRegistry",
    "BaseAudioInput",
    "PyAudioInput",
    "SpeechRecognitionInput",
    "create_audio_input",
    "get_available_engines",
    "get_or_create_audio_input",
]
