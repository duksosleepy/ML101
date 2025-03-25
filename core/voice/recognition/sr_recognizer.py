"""
Speech recognizer sử dụng SpeechRecognition.
"""

import asyncio

import numpy as np

from ..config import SR_AVAILABLE, logger
from .base import BaseRecognizer
from .registry import RecognizerRegistry

if SR_AVAILABLE:
    import speech_recognition as sr


class SpeechRecognitionRecognizer(BaseRecognizer):
    """
    Speech recognizer sử dụng SpeechRecognition library.
    Đây là lựa chọn dự phòng khi Vosk không khả dụng.
    Lưu ý: SpeechRecognition không hỗ trợ partial results.
    """

    # Khai báo tên engine cho registry
    engine_name = "sr"

    def __init__(self, sample_rate: int = 16000, language: str = "vi", **kwargs):
        super().__init__(sample_rate, language)
        self.recognizer = None
        self.initialize()

    def initialize(self):
        """
        Khởi tạo recognizer.
        """
        if not SR_AVAILABLE:
            logger.error("SpeechRecognition library not available")
            return

        try:
            self.recognizer = sr.Recognizer()
            logger.info("Initialized SpeechRecognition recognizer")
        except Exception as e:
            logger.error(f"Error initializing SpeechRecognition: {e}")
            self.recognizer = None

    def process_audio(self, audio_data: bytes) -> dict:
        """
        Xử lý audio với SpeechRecognition.

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
                "is_final": bool,   # luôn là True với SpeechRecognition
                "confidence": float # độ tin cậy (nếu có)
            }
        """
        if not self.is_available():
            return {"text": "", "is_final": True, "confidence": 0.0}

        result = {"text": "", "is_final": True, "confidence": 0.0}

        try:
            # Đảm bảo format audio là int16
            audio_data = self._ensure_int16_format(audio_data)

            # Chuyển bytes thành AudioData
            audio_source = sr.AudioData(
                audio_data,
                sample_rate=self.sample_rate,
                sample_width=2,  # int16 = 2 bytes
            )

            # Sử dụng Google Speech Recognition (có thể thay bằng các engine khác)
            text = self.recognizer.recognize_google(
                audio_source, language=self._map_language_code()
            )

            if text:
                result["text"] = text
                result["confidence"] = 1.0  # Google API không trả về confidence

        except sr.UnknownValueError:
            # Không nhận dạng được gì
            pass
        except sr.RequestError as e:
            logger.error(f"SpeechRecognition request error: {e}")
        except Exception as e:
            logger.error(f"Error processing audio with SpeechRecognition: {e}")

        return result

    async def process_audio_async(self, audio_data: bytes) -> dict:
        """
        Phiên bản bất đồng bộ của process_audio.
        """
        if not self.is_available():
            return {"text": "", "is_final": True, "confidence": 0.0}

        try:
            # Đảm bảo format audio là int16
            audio_data = self._ensure_int16_format(audio_data)

            # Chuyển bytes thành AudioData
            audio_source = sr.AudioData(
                audio_data,
                sample_rate=self.sample_rate,
                sample_width=2,  # int16 = 2 bytes
            )

            # Sử dụng asyncio.to_thread để không chặn main thread
            text = await asyncio.to_thread(
                self.recognizer.recognize_google,
                audio_source,
                language=self._map_language_code(),
            )

            if text:
                return {"text": text, "is_final": True, "confidence": 1.0}

        except sr.UnknownValueError:
            # Không nhận dạng được gì
            pass
        except sr.RequestError as e:
            logger.error(f"SpeechRecognition request error: {e}")
        except Exception as e:
            logger.error(f"Error processing audio with SpeechRecognition: {e}")

        return {"text": "", "is_final": True, "confidence": 0.0}

    def reset(self):
        """
        Reset recognizer.
        """
        if self.is_available():
            self.recognizer = sr.Recognizer()

    def is_available(self) -> bool:
        """
        Kiểm tra xem SpeechRecognition có sẵn sàng sử dụng không.

        Returns:
        --------
        bool
            True nếu có thể sử dụng, False nếu không
        """
        return SR_AVAILABLE and self.recognizer is not None

    def _map_language_code(self) -> str:
        """
        Chuyển đổi mã ngôn ngữ nội bộ sang định dạng mà Google Speech API hiểu.

        Returns:
        --------
        str
            Mã ngôn ngữ phù hợp với Google Speech API
        """
        language_mapping = {
            "vi": "vi-VN",
            "en": "en-US",
            # Thêm các ngôn ngữ khác ở đây
        }

        return language_mapping.get(self.language, "en-US")

    def _ensure_int16_format(self, audio_data: bytes) -> bytes:
        """
        Đảm bảo dữ liệu audio ở định dạng int16.
        SpeechRecognition yêu cầu dữ liệu ở định dạng int16.

        Parameters:
        -----------
        audio_data : bytes
            Dữ liệu audio cần chuyển đổi

        Returns:
        --------
        bytes
            Dữ liệu audio ở định dạng int16
        """
        try:
            # Kiểm tra nếu dữ liệu có vẻ là float32
            if len(audio_data) % 4 == 0:  # float32 = 4 bytes
                float_array = np.frombuffer(audio_data, dtype=np.float32)

                # Chuyển đổi sang int16
                float_array = np.clip(float_array, -1.0, 1.0)
                int16_array = (float_array * 32767).astype(np.int16)

                return int16_array.tobytes()

            # Nếu dữ liệu đã là int16
            if len(audio_data) % 2 == 0:  # int16 = 2 bytes
                return audio_data

            # Trường hợp khác
            logger.warning("Audio data format is neither float32 nor int16")
            return audio_data

        except Exception as e:
            logger.error(f"Error converting audio format: {e}")
            return audio_data


# Đăng ký recognizer với registry
RecognizerRegistry.register("sr", SpeechRecognitionRecognizer, lambda: SR_AVAILABLE)
