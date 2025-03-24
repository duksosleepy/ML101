"""
Mô hình session cho audio streaming và transcription.
"""

from collections import deque
from datetime import datetime
from typing import Dict, List, Optional

from ..config import logger
from ..models.schemas import AudioMetadata, TranscriptionConfig
from ..recognition.factory import create_recognizer


class AudioSession:
    """
    Lớp quản lý một phiên streaming audio và transcription.
    """

    def __init__(
        self,
        session_id: str,
        metadata: AudioMetadata = None,
        config: TranscriptionConfig = None,
    ):
        self.session_id = session_id
        self.created_at = datetime.now()
        self.last_activity = datetime.now()

        # Metadata
        if metadata is None:
            metadata = AudioMetadata()
        self.metadata = metadata

        # Config
        if config is None:
            config = TranscriptionConfig()
        self.config = config

        # Audio buffer và transcript
        self.audio_buffer = deque(maxlen=1000)  # Buffer audio
        self.raw_buffer = bytearray()  # Buffer raw cho Vosk
        self.transcript_buffer = []  # Buffer transcript
        self.current_transcript = ""  # Transcript hiện tại
        self.partial_transcript = ""  # Partial transcript

        # Trạng thái
        self.is_processing = False  # Đang xử lý hay không
        self.is_speaking = False  # Người dùng đang nói hay không
        self.silence_start = None  # Thời điểm bắt đầu im lặng

        # Thống kê
        self.packets_received = 0  # Số gói tin đã nhận
        self.total_bytes = 0  # Tổng số byte đã nhận
        self.total_audio_duration = 0  # Tổng thời lượng audio (giây)

        # Recognizer
        self.recognizer = None  # Speech recognizer
        self.create_recognizer()

    def update_activity(self):
        """Cập nhật thời gian hoạt động gần nhất."""
        self.last_activity = datetime.now()

    def create_recognizer(self):
        """Tạo speech recognizer phù hợp."""
        self.recognizer = create_recognizer(
            engine=self.config.engine,
            sample_rate=self.metadata.sample_rate,
            language=self.metadata.language,
            partial_results=self.config.partial_results,
            model_size=self.config.model_size,
        )

    def add_audio_chunk(self, chunk: bytes) -> int:
        """Thêm chunk audio vào buffer và trả về số byte đã thêm."""
        self.audio_buffer.append(chunk)
        self.raw_buffer.extend(chunk)
        self.packets_received += 1
        self.total_bytes += len(chunk)

        # Tính thời lượng audio dựa trên sample rate và kích thước chunk
        chunk_duration = len(chunk) / (
            self.metadata.sample_rate * 4
        )  # 4 bytes per float32 sample
        self.total_audio_duration += chunk_duration

        self.update_activity()
        return len(chunk)

    def get_audio_for_processing(self, window_size: float = None) -> bytes:
        """Lấy một đoạn audio từ buffer để xử lý."""
        if window_size is None:
            window_size = self.config.window_size

        # Tính số byte cần lấy dựa trên kích thước cửa sổ
        bytes_per_second = self.metadata.sample_rate * 4  # float32 = 4 bytes
        bytes_needed = int(window_size * bytes_per_second)

        # Nếu không đủ dữ liệu, trả về None
        if len(self.raw_buffer) < bytes_needed:
            return None

        # Lấy dữ liệu và loại bỏ phần đã xử lý, giữ lại phần chồng lấp
        overlap_bytes = int(self.config.buffer_overlap * bytes_per_second)
        process_bytes = bytes_needed - overlap_bytes

        result = bytes(self.raw_buffer[:bytes_needed])
        if process_bytes > 0:
            del self.raw_buffer[:process_bytes]

        return result

    def reset_buffers(self):
        """Reset các buffer."""
        self.audio_buffer.clear()
        self.raw_buffer = bytearray()

    def add_transcript(self, text: str, is_partial: bool = False):
        """Thêm transcript vào buffer."""
        if is_partial:
            self.partial_transcript = text
        elif text and text.strip():
            self.transcript_buffer.append(text)
            self.current_transcript = text
            self.partial_transcript = ""

    def get_transcript_history(self) -> List[str]:
        """Lấy lịch sử transcript."""
        return self.transcript_buffer

    def get_current_transcript(self) -> str:
        """Lấy transcript hiện tại (bao gồm cả partial nếu có)."""
        if self.partial_transcript:
            return f"{self.current_transcript} {self.partial_transcript}"
        return self.current_transcript


class SessionManager:
    """
    Quản lý các AudioSession.
    """

    def __init__(self):
        self.sessions: Dict[str, AudioSession] = {}

    def create_session(
        self,
        session_id: str,
        metadata: Optional[AudioMetadata] = None,
        config: Optional[TranscriptionConfig] = None,
    ) -> AudioSession:
        """Tạo session mới hoặc trả về session có sẵn."""
        if session_id in self.sessions:
            return self.sessions[session_id]

        session = AudioSession(session_id, metadata, config)
        self.sessions[session_id] = session
        logger.info(f"Created new session: {session_id}")
        return session

    def get_session(self, session_id: str) -> Optional[AudioSession]:
        """Lấy session theo ID."""
        return self.sessions.get(session_id)

    def delete_session(self, session_id: str):
        """Xóa session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Deleted session: {session_id}")

    def get_all_sessions(self) -> Dict[str, AudioSession]:
        """Lấy tất cả sessions."""
        return self.sessions


# Khởi tạo session manager toàn cục
session_manager = SessionManager()
