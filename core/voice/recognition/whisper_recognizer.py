"""
Speech recognizer sử dụng OpenAI Whisper.
"""

import time
from typing import Any, Dict

import numpy as np

from ..config import WHISPER_AVAILABLE, WHISPER_MODELS_DIR, logger
from .base import BaseRecognizer
from .registry import RecognizerRegistry

if WHISPER_AVAILABLE:
    import torch
    import whisper


class WhisperRecognizer(BaseRecognizer):
    """
    Speech recognizer sử dụng OpenAI Whisper.
    """

    # Khai báo tên engine cho registry
    engine_name = "whisper"

    def __init__(
        self,
        sample_rate: int = 16000,
        language: str = "vi",
        model_size: str = "small",
        device: str = None,
        compute_type: str = "float16",
        **kwargs,
    ):
        super().__init__(sample_rate, language)

        self.model_size = model_size
        self.device = device or (
            "cuda" if WHISPER_AVAILABLE and torch.cuda.is_available() else "cpu"
        )
        self.compute_type = compute_type

        # Các buffer cho streaming
        self.audio_buffer = np.array([], dtype=np.float32)
        self.text_buffer = ""
        self.last_transcript_time = time.time()

        # Khởi tạo
        self.model = None
        self.initialize()

    def initialize(self):
        """
        Khởi tạo model Whisper.
        """
        if not WHISPER_AVAILABLE:
            logger.error("Whisper library not available")
            return

        try:
            # Tải model Whisper
            # Model được lưu trong ~/.cache/whisper/
            logger.info(
                f"Loading Whisper model '{self.model_size}' on {self.device}..."
            )
            self.model = whisper.load_model(
                self.model_size,
                device=self.device,
                download_root=WHISPER_MODELS_DIR,
            )

            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Error initializing Whisper recognizer: {e}")
            self.model = None

    def process_audio(self, audio_data: bytes) -> dict:
        """
        Xử lý audio với Whisper.

        Parameters:
        -----------
        audio_data : bytes
            Dữ liệu audio cần xử lý

        Returns:
        --------
        dict
            Kết quả có dạng:
            {
                "text": str,        # văn bản nhận dạng được
                "is_final": bool,   # kết quả cuối cùng hay tạm thời
                "confidence": float # độ tin cậy (nếu có)
            }
        """
        if not self.is_available():
            return {"text": "", "is_final": True, "confidence": 0.0}

        result = {"text": "", "is_final": True, "confidence": 0.0}

        try:
            # Chuyển đổi bytes thành float32 numpy array
            float_array = np.frombuffer(audio_data, dtype=np.float32)

            # Thêm vào buffer
            self.audio_buffer = np.append(self.audio_buffer, float_array)

            # Xác định khi nào transcribe
            current_time = time.time()
            buffer_duration = len(self.audio_buffer) / self.sample_rate
            time_since_last = current_time - self.last_transcript_time

            # Nếu đủ dữ liệu (ít nhất 1 giây audio) hoặc đã quá 3 giây từ lần cuối
            if buffer_duration >= 1.0 or (
                buffer_duration > 0.2 and time_since_last > 3.0
            ):
                # Sử dụng Whisper transcribe
                audio_np = self.audio_buffer

                # Chuẩn hóa audio theo yêu cầu của Whisper
                if np.max(np.abs(audio_np)) > 1.0:
                    audio_np = audio_np / np.max(np.abs(audio_np))

                transcription = self.model.transcribe(
                    audio_np,
                    language=self._map_language_code(),
                    fp16=(self.compute_type == "float16"),
                    temperature=0.0,  # Càng thấp càng ổn định
                )

                text = transcription.get("text", "").strip()

                if text:
                    result["text"] = text
                    result["is_final"] = True

                    # Thêm vào buffer text (nếu cần tích lũy)
                    # self.text_buffer += " " + text if self.text_buffer else text

                    # Reset audio buffer
                    self.audio_buffer = np.array([], dtype=np.float32)
                    self.last_transcript_time = current_time

        except Exception as e:
            logger.error(f"Error processing audio with Whisper: {e}")

        return result

    def transcribe_file(self, file_path: str) -> Dict[str, Any]:
        """
        Transcribe audio từ file.

        Parameters:
        -----------
        file_path : str
            Đường dẫn đến file audio

        Returns:
        --------
        Dict[str, Any]
            Kết quả transcription
        """
        if not self.is_available():
            return {"text": "", "segments": []}

        try:
            result = self.model.transcribe(
                file_path,
                language=self._map_language_code(),
                fp16=(self.compute_type == "float16"),
            )
            return result
        except Exception as e:
            logger.error(f"Error transcribing file with Whisper: {e}")
            return {"text": "", "segments": []}

    def reset(self):
        """
        Reset trạng thái của recognizer.
        """
        self.audio_buffer = np.array([], dtype=np.float32)
        self.text_buffer = ""
        self.last_transcript_time = time.time()

    def is_available(self) -> bool:
        """
        Kiểm tra xem Whisper có sẵn sàng sử dụng không.

        Returns:
        --------
        bool
            True nếu có thể sử dụng, False nếu không
        """
        return WHISPER_AVAILABLE and self.model is not None

    def _map_language_code(self) -> str:
        """
        Chuyển đổi mã ngôn ngữ nội bộ sang định dạng mà Whisper hiểu.

        Returns:
        --------
        str
            Mã ngôn ngữ phù hợp với Whisper
        """
        # Whisper sử dụng các mã ngôn ngữ như "vi", "en" trực tiếp
        # nên chúng ta chỉ cần trả về mã ngôn ngữ như đã có
        return self.language


# Đăng ký recognizer với registry
RecognizerRegistry.register(
    "whisper", WhisperRecognizer, lambda: WHISPER_AVAILABLE
)
