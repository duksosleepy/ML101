"""
Speech recognizer sử dụng Vosk.
"""

import json
import os

import numpy as np

from ..config import MODELS_DIR, VOSK_AVAILABLE, VOSK_MODEL_MAPPING, logger
from .base import BaseRecognizer
from .registry import RecognizerRegistry

if VOSK_AVAILABLE:
    from vosk import KaldiRecognizer, Model


class VoskRecognizer(BaseRecognizer):
    """
    Speech recognizer sử dụng Vosk.
    """

    # Khai báo tên engine cho registry
    engine_name = "vosk"

    def __init__(
        self,
        sample_rate: int = 16000,
        language: str = "vi",
        partial_results: bool = True,
        **kwargs,
    ):
        super().__init__(sample_rate, language)
        self.partial_results = partial_results
        self.model = None
        self.recognizer = None
        self.initialize()

    def initialize(self):
        """
        Khởi tạo model và recognizer.
        """
        if not VOSK_AVAILABLE:
            logger.error("Vosk library not available")
            return

        try:
            # Lấy model phù hợp với ngôn ngữ
            model_name = VOSK_MODEL_MAPPING.get(
                self.language, VOSK_MODEL_MAPPING.get("en")
            )
            model_path = os.path.join(MODELS_DIR, "vosk_models", model_name)

            # Kiểm tra model có tồn tại không
            if not os.path.exists(model_path):
                logger.warning(f"Vosk model {model_path} not found.")
                fallback_model = os.path.join(
                    MODELS_DIR, "vosk_models", VOSK_MODEL_MAPPING.get("en")
                )

                if os.path.exists(fallback_model):
                    logger.warning(f"Using fallback model: {fallback_model}")
                    model_path = fallback_model
                else:
                    logger.error(
                        f"No models found in {MODELS_DIR}. Please download models from https://alphacephei.com/vosk/models"
                    )
                    return

            # Tạo model và recognizer
            self.model = Model(model_path)
            self.recognizer = KaldiRecognizer(self.model, self.sample_rate)

            # Cấu hình Vosk cho partial results
            self.recognizer.SetPartialWords(self.partial_results)
            self.recognizer.SetMaxAlternatives(0)

            logger.info(f"Initialized Vosk recognizer with model {model_path}")
        except Exception as e:
            logger.error(f"Error initializing Vosk recognizer: {e}")
            self.model = None
            self.recognizer = None

    def process_audio(self, audio_data: bytes) -> dict:
        """
        Xử lý audio với Vosk.

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

        result = {"text": "", "is_final": False, "confidence": 0.0}

        try:
            # Chuyển đổi sang int16 nếu cần
            audio_data = self._ensure_int16(audio_data)

            # Xử lý với Vosk
            if self.recognizer.AcceptWaveform(audio_data):
                # Kết quả hoàn chỉnh
                result_json = self.recognizer.Result()
                result_obj = json.loads(result_json)

                if "text" in result_obj and result_obj["text"].strip():
                    result["text"] = result_obj["text"]
                    result["is_final"] = True
                    if "confidence" in result_obj:
                        result["confidence"] = result_obj["confidence"]

            elif self.partial_results:
                # Kết quả tạm thời
                partial_json = self.recognizer.PartialResult()
                partial_obj = json.loads(partial_json)

                if "partial" in partial_obj and partial_obj["partial"].strip():
                    result["text"] = partial_obj["partial"]
                    result["is_final"] = False

        except Exception as e:
            logger.error(f"Error processing audio with Vosk: {e}")

        return result

    def reset(self):
        """
        Reset recognizer.
        """
        if self.is_available():
            # Tạo recognizer mới
            self.recognizer = KaldiRecognizer(self.model, self.sample_rate)
            self.recognizer.SetPartialWords(self.partial_results)
            self.recognizer.SetMaxAlternatives(0)

    def is_available(self) -> bool:
        """
        Kiểm tra xem Vosk có sẵn sàng sử dụng không.

        Returns:
        --------
        bool
            True nếu có thể sử dụng, False nếu không
        """
        return VOSK_AVAILABLE and self.recognizer is not None

    def _ensure_int16(self, audio_data: bytes) -> bytes:
        """
        Đảm bảo audio data có định dạng int16.
        Vosk yêu cầu dữ liệu audio phải ở dạng int16.

        Parameters:
        -----------
        audio_data : bytes
            Dữ liệu audio cần chuyển đổi

        Returns:
        --------
        bytes
            Dữ liệu audio đã chuyển đổi sang int16
        """
        try:
            # Kiểm tra xem dữ liệu đã ở dạng int16 chưa
            if len(audio_data) % 2 == 0:
                # Thử parsing một vài mẫu để kiểm tra
                test_samples = np.frombuffer(audio_data[:10], dtype=np.int16)
                if np.max(np.abs(test_samples)) > 0:
                    # Có vẻ như đã ở dạng int16, không cần chuyển đổi
                    return audio_data

            # Chuyển đổi từ float32 sang int16
            float_array = np.frombuffer(audio_data, dtype=np.float32)

            # Chuẩn hóa và chuyển đổi sang int16
            float_array = np.clip(float_array, -1.0, 1.0)
            int16_array = (float_array * 32767).astype(np.int16)

            # Chuyển đổi trở lại thành bytes
            return int16_array.tobytes()

        except Exception as e:
            logger.error(f"Error converting to int16: {e}")
            return audio_data


# Đăng ký recognizer với registry
RecognizerRegistry.register("vosk", VoskRecognizer, lambda: VOSK_AVAILABLE)
