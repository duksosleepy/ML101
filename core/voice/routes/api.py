"""
REST API endpoints để quản lý session và lấy transcript.
"""

import asyncio
import os
import tempfile
import time

from fastapi import (
    APIRouter,
    BackgroundTasks,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)

from ..config import SR_AVAILABLE, VOSK_AVAILABLE, WHISPER_AVAILABLE, logger
from ..models import (
    HealthResponse,
    SessionInfo,
    TranscriptResponse,
    session_manager,
)
from ..recognition import create_recognizer
from .websocket import active_connections

router = APIRouter(tags=["audio"])


@router.get("/audio/{session_id}/info", response_model=SessionInfo)
async def get_session_info(session_id: str):
    """
    Lấy thông tin về session.

    Parameters:
    -----------
    session_id : str
        ID của session

    Returns:
    --------
    SessionInfo
        Thông tin về session
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    # Trả về thông tin (không bao gồm audio chunks)
    return {
        "session_id": session_id,
        "created_at": session.created_at.isoformat(),
        "last_activity": session.last_activity.isoformat(),
        "sample_rate": session.metadata.sample_rate,
        "channels": session.metadata.channels,
        "encoding": session.metadata.encoding,
        "language": session.metadata.language,
        "transcript": session.get_transcript_history(),
        "current_transcript": session.get_current_transcript(),
        "packets_received": session.packets_received,
        "is_active": session_id in active_connections,
        "is_processing": session.is_processing,
        "is_speaking": session.is_speaking,
        "config": {
            "engine": session.config.engine,
            "model_size": session.config.model_size,
            "partial_results": session.config.partial_results,
            "vad_enabled": session.config.vad_enabled,
            "vad_threshold": session.config.vad_threshold,
            "silence_duration": session.config.silence_duration,
            "window_size": session.config.window_size,
            "buffer_overlap": session.config.buffer_overlap,
        },
    }


@router.get("/audio/{session_id}/transcript", response_model=TranscriptResponse)
async def get_transcript(session_id: str):
    """
    Lấy transcript của session.

    Parameters:
    -----------
    session_id : str
        ID của session

    Returns:
    --------
    TranscriptResponse
        Transcript của session
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    return {
        "session_id": session_id,
        "transcript_history": session.get_transcript_history(),
        "current_transcript": session.get_current_transcript(),
    }


@router.post("/transcribe")
async def transcribe_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    language: str = Form("vi"),
    engine: str = Form("auto"),
    model_size: str = Form("small"),
):
    """
    Transcribe audio file đã tải lên.

    Parameters:
    -----------
    file : UploadFile
        File audio cần transcribe
    language : str
        Mã ngôn ngữ (vi, en, etc.)
    engine : str
        Engine nhận dạng (whisper, vosk, auto)
    model_size : str
        Kích thước model (chỉ áp dụng cho Whisper)

    Returns:
    --------
    dict
        Kết quả transcription
    """
    # Kiểm tra các engine có sẵn
    if engine == "whisper" and not WHISPER_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Whisper is not available. Please install with: pip install openai-whisper",
        )

    if engine == "vosk" and not VOSK_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vosk is not available. Please install with: pip install vosk",
        )

    # Tạo thư mục tạm để lưu file
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, file.filename)

    try:
        # Lưu file tạm
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Tạo recognizer
        recognizer = create_recognizer(
            engine=engine, language=language, model_size=model_size
        )

        if not recognizer:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create recognizer",
            )

        # Xử lý transcription tùy thuộc vào loại recognizer
        if hasattr(recognizer, "transcribe_file"):
            # Dùng hàm transcribe_file nếu có (Whisper)
            result = await asyncio.to_thread(recognizer.transcribe_file, file_path)

            # Dọn dẹp file
            background_tasks.add_task(
                lambda: os.remove(file_path) if os.path.exists(file_path) else None
            )
            background_tasks.add_task(
                lambda: os.rmdir(temp_dir) if os.path.exists(temp_dir) else None
            )

            return {
                "text": result.get("text", ""),
                "segments": result.get("segments", []),
                "language": result.get("language", language),
                "engine": engine,
            }
        # Xử lý theo từng khúc với các engine khác
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"Transcription for file not implemented for engine: {engine}",
        )

    except Exception as e:
        # Dọn dẹp file trong trường hợp lỗi
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)

        logger.error(f"Error transcribing file: {e}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error transcribing file: {e!s}",
        )


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Endpoint kiểm tra trạng thái hoạt động của server.

    Returns:
    --------
    HealthResponse
        Thông tin về trạng thái server
    """
    return {
        "status": "ok",
        "timestamp": time.time(),
        "active_connections": len(active_connections),
        "active_sessions": len(session_manager.get_all_sessions()),
        "engines_available": {
            "vosk": VOSK_AVAILABLE,
            "whisper": WHISPER_AVAILABLE,
            "speech_recognition": SR_AVAILABLE,
        },
    }
