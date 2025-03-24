"""
Cấu hình toàn cục cho ứng dụng Audio Streaming API.
"""

import logging
import os
from pathlib import Path

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Đường dẫn thư mục
BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = os.path.join(BASE_DIR, "models")
VOSK_MODELS_DIR = os.path.join(MODELS_DIR, "vosk_models")
WHISPER_MODELS_DIR = os.path.join(MODELS_DIR, "whisper_models")

# Đảm bảo thư mục models tồn tại
os.makedirs(VOSK_MODELS_DIR, exist_ok=True)
os.makedirs(WHISPER_MODELS_DIR, exist_ok=True)

# Cấu hình Vosk
DEFAULT_VOSK_MODEL = "vosk-model-small-en-us-0.15"
VOSK_MODEL_MAPPING = {
    "vi": "vosk-model-vi",
    "en": "vosk-model-small-en-us-0.15",
}

# Cấu hình Whisper
DEFAULT_WHISPER_MODEL_SIZE = (
    "small"  # tiny, base, small, medium, large, large-v2
)
WHISPER_AVAILABLE_MODELS = [
    "tiny",
    "base",
    "small",
    "medium",
    "large",
    "large-v2",
]

# Cấu hình audio
DEFAULT_SAMPLE_RATE = 16000
DEFAULT_CHANNELS = 1

# Cấu hình session
SESSION_CLEANUP_INTERVAL = 60  # seconds
SESSION_MAX_AGE = 30  # minutes

# Kiểm tra packages có sẵn
try:
    from vosk import KaldiRecognizer, Model, SetLogLevel

    VOSK_AVAILABLE = True
    # Giảm log output của Vosk
    SetLogLevel(-1)
except ImportError:
    VOSK_AVAILABLE = False
    logger.warning("Vosk not available. Install with: pip install vosk")

try:
    import speech_recognition as sr

    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False
    logger.warning(
        "SpeechRecognition not available. Install with: pip install SpeechRecognition"
    )

try:
    import torch
    import whisper

    WHISPER_AVAILABLE = True
    WHISPER_GPU_AVAILABLE = torch.cuda.is_available()
    if WHISPER_GPU_AVAILABLE:
        logger.info(f"Whisper will use GPU: {torch.cuda.get_device_name(0)}")
    else:
        logger.info("Whisper will use CPU (GPU not available)")
except ImportError:
    WHISPER_AVAILABLE = False
    WHISPER_GPU_AVAILABLE = False
    logger.warning(
        "Whisper not available. Install with: pip install openai-whisper"
    )

# Kiểm tra nếu không có engine nào sẵn sàng
if not (VOSK_AVAILABLE or SR_AVAILABLE or WHISPER_AVAILABLE):
    logger.error(
        "No speech recognition engine available! Please install vosk, SpeechRecognition, or whisper."
    )
