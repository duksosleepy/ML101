"""
Module chứa các speech recognizer.
"""

# Import các lớp cơ sở trước để các lớp con có thể kế thừa
from .base import BaseRecognizer

# Import factory functions
from .factory import (
    create_recognizer,
    get_available_engines,
    get_or_create_recognizer,
)
from .registry import RecognizerRegistry
from .sr_recognizer import SpeechRecognitionRecognizer

# Import các recognizer cụ thể
# Các recognizer này sẽ tự động đăng ký với Registry
from .vosk_recognizer import VoskRecognizer
from .whisper_recognizer import WhisperRecognizer

__all__ = [
    "BaseRecognizer",
    "RecognizerRegistry",
    "VoskRecognizer",
    "SpeechRecognitionRecognizer",
    "WhisperRecognizer",
    "create_recognizer",
    "get_or_create_recognizer",
    "get_available_engines",
]
