"""
Audio input processor sử dụng SpeechRecognition.
"""

import threading
import time
from typing import Any

from ..config import logger
from .base import BaseAudioInput
from .registry import AudioInputRegistry

# Kiểm tra SpeechRecognition có sẵn không
try:
    import speech_recognition as sr

    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False
    logger.warning(
        "SpeechRecognition not available. Install with: pip install SpeechRecognition"
    )


class SpeechRecognitionInput(BaseAudioInput):
    """
    Audio input processor sử dụng SpeechRecognition.
    """

    # Khai báo tên engine cho registry
    engine_name = "sr"

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        device_index: int | None = None,
        chunk_duration: float = 0.5,
        **kwargs,
    ):
        super().__init__(sample_rate, channels, **kwargs)

        self.device_index = device_index
        self.chunk_duration = chunk_duration  # Duration of each audio chunk in seconds
        self.chunk_samples = int(self.sample_rate * self.chunk_duration)

        self.recognizer = None
        self.microphone = None
        self.thread = None
        self.stop_event = None

        # Khởi tạo SpeechRecognition nếu có thể
        if SR_AVAILABLE:
            try:
                self.recognizer = sr.Recognizer()
                self.microphone = sr.Microphone(
                    device_index=device_index, sample_rate=sample_rate
                )
                self.stop_event = threading.Event()
            except Exception as e:
                logger.error(f"Error initializing SpeechRecognition: {e}")

    def get_device_list(self) -> list[dict[str, Any]]:
        """
        Lấy danh sách thiết bị âm thanh.

        Returns:
        --------
        List[Dict[str, Any]]
            Danh sách thiết bị
        """
        if not SR_AVAILABLE:
            return []

        devices = []
        try:
            for i, name in enumerate(sr.Microphone.list_microphone_names()):
                devices.append(
                    {
                        "index": i,
                        "name": name,
                        "channels": None,  # SpeechRecognition doesn't provide this info
                        "sample_rate": None,  # SpeechRecognition doesn't provide this info
                        "latency": None,  # SpeechRecognition doesn't provide this info
                    }
                )
        except Exception as e:
            logger.error(f"Error getting device list: {e}")

        return devices

    def _record_thread(self):
        """
        Thread để thu âm liên tục.
        """
        try:
            with self.microphone as source:
                # Điều chỉnh cho nhiễu môi trường
                self.recognizer.adjust_for_ambient_noise(source, duration=1)

                # Sử dụng non-blocking record
                stop_recording = False

                while self.is_running and not stop_recording:
                    try:
                        # Nhận audio non-blocking để có thể dừng khi cần
                        audio_data = self.recognizer.listen(
                            source,
                            timeout=1.0,  # Timeout sau 1 giây nếu không có âm thanh
                            phrase_time_limit=self.chunk_duration,  # Giới hạn thời gian mỗi đoạn
                        )

                        # Kiểm tra xem cờ dừng đã được thiết lập chưa
                        if not self.is_running or self.stop_event.is_set():
                            stop_recording = True
                            break

                        # Lấy raw data từ AudioData và chuyển vào các callback
                        raw_data = audio_data.get_raw_data(
                            convert_rate=self.sample_rate,
                            convert_width=2,  # 16-bit audio (2 bytes)
                        )

                        self.process_audio_data(raw_data)

                    except sr.WaitTimeoutError:
                        # Không có âm thanh, tiếp tục vòng lặp
                        pass
                    except Exception as e:
                        logger.error(f"Error recording audio: {e}")
                        if not self.is_running:
                            break
                        time.sleep(0.1)  # Tránh CPU spike nếu có lỗi

        except Exception as e:
            logger.error(f"Error in recording thread: {e}")
        finally:
            self.is_running = False

    def start(self):
        """
        Bắt đầu thu âm.
        """
        if not self.is_available():
            logger.error("SpeechRecognition is not available")
            return False

        if self.is_running:
            logger.warning("Already recording")
            return True

        try:
            self.is_running = True
            self.stop_event.clear()
            self.thread = threading.Thread(target=self._record_thread)
            self.thread.daemon = True
            self.thread.start()
            return True
        except Exception as e:
            logger.error(f"Error starting recording: {e}")
            self.is_running = False
            return False

    def stop(self):
        """
        Dừng thu âm.
        """
        self.is_running = False

        # Thiết lập cờ dừng
        if self.stop_event:
            self.stop_event.set()

        # Đợi thread kết thúc
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
            self.thread = None

    def is_available(self) -> bool:
        """
        Kiểm tra xem SpeechRecognition có sẵn sàng sử dụng không.

        Returns:
        --------
        bool
            True nếu sẵn sàng, False nếu không
        """
        return (
            SR_AVAILABLE and self.recognizer is not None and self.microphone is not None
        )

    def __del__(self):
        """
        Giải phóng tài nguyên khi đối tượng bị hủy.
        """
        self.stop()


# Đăng ký audio input với registry
AudioInputRegistry.register("sr", SpeechRecognitionInput, lambda: SR_AVAILABLE)
