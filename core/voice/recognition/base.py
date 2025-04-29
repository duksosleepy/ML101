"""
Lớp cơ sở cho các speech recognizer.
"""

from abc import ABC, abstractmethod
from typing import Any, ClassVar


class BaseRecognizer(ABC):
    """
    Lớp trừu tượng cho các speech recognizer.
    Các lớp con cần triển khai các phương thức này.
    """

    # Tên của engine, được ghi đè bởi lớp con
    engine_name: ClassVar[str] = "base"

    def __init__(
        self, sample_rate: int = 16000, language: str = "vi", **kwargs
    ):
        self.sample_rate = sample_rate
        self.language = language

    @classmethod
    def get_engine_name(cls) -> str:
        """
        Lấy tên của engine nhận dạng.

        Returns:
        --------
        str
            Tên của engine
        """
        return cls.engine_name

    @abstractmethod
    def process_audio(self, audio_data: bytes) -> dict[str, Any]:
        """
        Xử lý audio data và trả về kết quả nhận dạng.

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

    @abstractmethod
    def reset(self):
        """
        Reset trạng thái của recognizer.
        """

    @abstractmethod
    def is_available(self) -> bool:
        """
        Kiểm tra xem recognizer có sẵn sàng sử dụng không.

        Returns:
        --------
        bool
            True nếu có thể sử dụng, False nếu không
        """
