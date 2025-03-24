"""
Lớp cơ sở cho thu âm từ microphone.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, ClassVar, Dict, List


class BaseAudioInput(ABC):
    """
    Lớp cơ sở cho các audio input processor.
    """

    # Tên của engine, được ghi đè bởi lớp con
    engine_name: ClassVar[str] = "base"

    def __init__(self, sample_rate: int = 16000, channels: int = 1, **kwargs):
        self.sample_rate = sample_rate
        self.channels = channels
        self.is_running = False
        self.callbacks = []

    @classmethod
    def get_engine_name(cls) -> str:
        """
        Lấy tên của engine audio input.

        Returns:
        --------
        str
            Tên của engine
        """
        return cls.engine_name

    def add_callback(self, callback: Callable[[bytes], None]):
        """
        Thêm callback function để xử lý dữ liệu audio.

        Parameters:
        -----------
        callback : Callable[[bytes], None]
            Function sẽ được gọi khi có dữ liệu audio mới
        """
        self.callbacks.append(callback)

    def process_audio_data(self, audio_data: bytes):
        """
        Xử lý dữ liệu audio bằng cách gọi các callback.

        Parameters:
        -----------
        audio_data : bytes
            Dữ liệu audio cần xử lý
        """
        for callback in self.callbacks:
            try:
                callback(audio_data)
            except Exception as e:
                print(f"Error in audio callback: {e}")

    @abstractmethod
    def start(self):
        """
        Bắt đầu thu âm.
        """

    @abstractmethod
    def stop(self):
        """
        Dừng thu âm.
        """

    @abstractmethod
    def get_device_list(self) -> List[Dict[str, Any]]:
        """
        Lấy danh sách thiết bị âm thanh.

        Returns:
        --------
        List[Dict[str, Any]]
            Danh sách thiết bị
        """

    @abstractmethod
    def is_available(self) -> bool:
        """
        Kiểm tra xem audio input có sẵn sàng sử dụng không.

        Returns:
        --------
        bool
            True nếu sẵn sàng, False nếu không
        """
