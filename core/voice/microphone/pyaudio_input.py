"""
Audio input processor sử dụng PyAudio.
"""

import threading
import time
from typing import Any

from ..config import logger
from .base import BaseAudioInput
from .registry import AudioInputRegistry

# Kiểm tra PyAudio có sẵn không
try:
    import pyaudio

    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    logger.warning("PyAudio not available. Install with: pip install pyaudio")


class PyAudioInput(BaseAudioInput):
    """
    Audio input processor sử dụng PyAudio.
    """

    # Khai báo tên engine cho registry
    engine_name = "pyaudio"

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        format: int = None,
        frames_per_buffer: int = 4096,
        device_index: int | None = None,
        **kwargs,
    ):
        super().__init__(sample_rate, channels, **kwargs)

        self.format = format or (pyaudio.paInt16 if PYAUDIO_AVAILABLE else None)
        self.frames_per_buffer = frames_per_buffer
        self.device_index = device_index

        self.audio = None
        self.stream = None
        self.thread = None

        # Khởi tạo PyAudio nếu có thể
        if PYAUDIO_AVAILABLE:
            try:
                self.audio = pyaudio.PyAudio()
            except Exception as e:
                logger.error(f"Error initializing PyAudio: {e}")

    def get_device_list(self) -> list[dict[str, Any]]:
        """
        Lấy danh sách thiết bị âm thanh.

        Returns:
        --------
        List[Dict[str, Any]]
            Danh sách thiết bị
        """
        if not self.is_available():
            return []

        devices = []
        try:
            info = self.audio.get_host_api_info_by_index(0)
            num_devices = info.get("deviceCount")

            for i in range(num_devices):
                device_info = self.audio.get_device_info_by_host_api_device_index(0, i)
                if device_info.get("maxInputChannels") > 0:  # Chỉ lấy input devices
                    devices.append(
                        {
                            "index": i,
                            "name": device_info.get("name"),
                            "channels": device_info.get("maxInputChannels"),
                            "sample_rate": int(device_info.get("defaultSampleRate")),
                            "latency": device_info.get("defaultLowInputLatency"),
                        }
                    )
        except Exception as e:
            logger.error(f"Error getting device list: {e}")

        return devices

    def _audio_callback(self, in_data, frame_count, time_info, status):
        """
        Callback được gọi bởi PyAudio khi có dữ liệu audio mới.
        """
        if self.is_running:
            self.process_audio_data(in_data)
        return (None, pyaudio.paContinue)

    def _record_thread(self):
        """
        Thread để thu âm liên tục.
        """
        try:
            # Mở stream
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.frames_per_buffer,
                stream_callback=self._audio_callback if self.callbacks else None,
            )

            # Nếu không có callback, đọc dữ liệu thủ công
            if not self.callbacks:
                self.stream.start_stream()
                while self.is_running:
                    try:
                        data = self.stream.read(
                            self.frames_per_buffer, exception_on_overflow=False
                        )
                        self.process_audio_data(data)
                    except Exception as e:
                        logger.error(f"Error reading from stream: {e}")
                        if not self.is_running:
                            break
                        time.sleep(0.1)  # Tránh CPU spike nếu có lỗi

            # Nếu có callback, stream đã tự động bắt đầu
            else:
                while self.is_running and self.stream.is_active():
                    time.sleep(0.1)  # Ngủ để tránh CPU spike

        except Exception as e:
            logger.error(f"Error in recording thread: {e}")
        finally:
            self.stop()

    def start(self):
        """
        Bắt đầu thu âm.
        """
        if not self.is_available():
            logger.error("PyAudio is not available")
            return False

        if self.is_running:
            logger.warning("Already recording")
            return True

        try:
            self.is_running = True
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

        # Dừng và đóng stream nếu đang mở
        if self.stream:
            try:
                if self.stream.is_active():
                    self.stream.stop_stream()
                self.stream.close()
            except Exception as e:
                logger.error(f"Error closing stream: {e}")
            finally:
                self.stream = None

        # Đợi thread kết thúc
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
            self.thread = None

    def is_available(self) -> bool:
        """
        Kiểm tra xem PyAudio có sẵn sàng sử dụng không.

        Returns:
        --------
        bool
            True nếu sẵn sàng, False nếu không
        """
        return PYAUDIO_AVAILABLE and self.audio is not None

    def __del__(self):
        """
        Giải phóng tài nguyên khi đối tượng bị hủy.
        """
        self.stop()

        # Đóng PyAudio
        if self.audio:
            try:
                self.audio.terminate()
            except:
                pass


# Đăng ký audio input với registry
AudioInputRegistry.register("pyaudio", PyAudioInput, lambda: PYAUDIO_AVAILABLE)
