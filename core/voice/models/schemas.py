"""
Pydantic schemas để xác thực và chuyển đổi dữ liệu.
"""

from typing import Any

from pydantic import BaseModel


class AudioMetadata(BaseModel):
    """Metadata của audio stream."""

    sample_rate: int = 16000
    channels: int = 1
    encoding: str = "float32"
    language: str = "vi"  # Ngôn ngữ mặc định


class TranscriptionConfig(BaseModel):
    """Cấu hình cho quá trình transcription."""

    engine: str = "auto"  # auto, vosk, whisper, speechrecognition
    model_size: str = "small"  # tiny, base, small, medium, large (cho Whisper)
    partial_results: bool = True  # Gửi kết quả tạm thời
    vad_enabled: bool = True  # Voice Activity Detection
    vad_threshold: float = 0.3  # Ngưỡng phát hiện giọng nói
    silence_duration: float = 0.5  # Thời gian im lặng để ngắt câu (giây)
    buffer_overlap: float = 0.25  # Độ chồng lấp của buffer (giây)
    window_size: float = 0.5  # Kích thước cửa sổ xử lý (giây)


class SessionInfo(BaseModel):
    """Thông tin về một session."""

    session_id: str
    created_at: str
    last_activity: str
    sample_rate: int
    channels: int
    encoding: str
    language: str
    transcript: list[str]
    current_transcript: str
    packets_received: int
    is_active: bool
    is_processing: bool
    is_speaking: bool
    config: dict[str, Any]


class TranscriptResponse(BaseModel):
    """Phản hồi về transcript của session."""

    session_id: str
    transcript_history: list[str]
    current_transcript: str


class HealthResponse(BaseModel):
    """Phản hồi về trạng thái hoạt động của server."""

    status: str
    timestamp: float
    active_connections: int
    active_sessions: int
    engines_available: dict[str, bool]


class WebSocketMessage(BaseModel):
    """Message được gửi qua WebSocket."""

    type: str
    data: dict[str, Any] | None = None
    timestamp: float | None = None


class TranscriptResult(BaseModel):
    """Kết quả transcription."""

    text: str
    is_final: bool = True
    timestamp: float
