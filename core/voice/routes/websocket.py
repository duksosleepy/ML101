"""
WebSocket endpoints để streaming audio.
"""

import asyncio
import json
import time
from typing import Dict

from fastapi import WebSocket, WebSocketDisconnect

from ..config import SR_AVAILABLE, VOSK_AVAILABLE, logger
from ..models import (
    AudioMetadata,
    TranscriptionConfig,
    session_manager,
)
from ..utils import detect_voice_activity

# Lưu trữ các kết nối WebSocket đang hoạt động
active_connections: Dict[str, WebSocket] = {}

# Lưu trữ task transcription đang chạy
active_transcription_tasks: Dict[str, asyncio.Task] = {}


async def process_audio_vosk(session_id: str, websocket: WebSocket):  # noqa: C901
    """
    Xử lý audio với Vosk và gửi transcript về client.

    Parameters:
    -----------
    session_id : str
        ID của session
    websocket : WebSocket
        WebSocket connection để gửi kết quả về client
    """
    try:
        # Lấy session
        session = session_manager.get_session(session_id)
        if not session:
            logger.error(f"Session {session_id} not found")
            return

        # Đánh dấu đang xử lý
        session.is_processing = True

        while True:
            # Lấy dữ liệu audio để xử lý
            audio_data = session.get_audio_for_processing()
            if audio_data is None:
                # Không đủ dữ liệu, đợi thêm
                await asyncio.sleep(0.1)
                continue

            # Kiểm tra Voice Activity
            if session.config.vad_enabled:
                has_voice, energy = detect_voice_activity(
                    audio_data, session.config.vad_threshold
                )

                # Xử lý logic im lặng/nói
                current_time = time.time()
                if has_voice:
                    session.is_speaking = True
                    session.silence_start = None
                elif session.is_speaking:
                    # Bắt đầu đếm thời gian im lặng
                    if session.silence_start is None:
                        session.silence_start = current_time
                    elif (
                        current_time - session.silence_start
                        > session.config.silence_duration
                    ):
                        # Im lặng đủ lâu, xác định là hết câu
                        session.is_speaking = False

                        # Reset recognizer để bắt đầu câu mới
                        if session.recognizer:
                            session.recognizer.reset()

            # Xử lý audio bằng recognizer
            if session.recognizer:
                result = session.recognizer.process_audio(audio_data)

                if result["text"]:
                    # Thêm vào transcript
                    session.add_transcript(
                        result["text"], is_partial=not result["is_final"]
                    )

                    # Gửi về client
                    await websocket.send_json(
                        {
                            "type": "transcript",
                            "text": result["text"],
                            "is_final": result["is_final"],
                            "timestamp": time.time() * 1000,
                        }
                    )

            # Đợi một chút để không tốn quá nhiều CPU
            await asyncio.sleep(0.05)

    except asyncio.CancelledError:
        logger.info(f"Transcription task cancelled for session {session_id}")
    except Exception as e:
        logger.error(f"Error processing audio: {e}")
        try:
            await websocket.send_json(
                {
                    "type": "error",
                    "message": f"Transcription error: {str(e)}",
                    "timestamp": time.time() * 1000,
                }
            )
        except:
            pass
    finally:
        # Đánh dấu đã xử lý xong
        session = session_manager.get_session(session_id)
        if session:
            session.is_processing = False


async def process_client_message(websocket: WebSocket, session_id: str) -> bool:  # noqa: C901
    """
    Xử lý tin nhắn đến từ client.

    Parameters:
    -----------
    websocket : WebSocket
        WebSocket connection
    session_id : str
        ID của session

    Returns:
    --------
    bool
        True nếu xử lý thành công, False nếu có lỗi kết nối
    """
    try:
        # Lấy session
        session = session_manager.get_session(session_id)
        if not session:
            logger.error(f"Session {session_id} not found")
            return False

        # Nhận tin nhắn
        data = await websocket.receive()

        # Xử lý tin nhắn text (JSON)
        if "text" in data:
            try:
                message = json.loads(data["text"])
                message_type = message.get("type", "")

                # Xử lý tin nhắn ping
                if message_type == "ping":
                    await websocket.send_json(
                        {"type": "pong", "timestamp": message.get("timestamp")}
                    )

                # Xử lý cập nhật metadata
                elif message_type == "metadata":
                    metadata = AudioMetadata(**message.get("data", {}))
                    session.metadata = metadata

                    # Cập nhật recognizer nếu cần
                    session.create_recognizer()

                    logger.info(
                        f"Updated metadata for session {session_id}: {metadata}"
                    )

                # Xử lý cập nhật config
                elif message_type == "config":
                    config = TranscriptionConfig(**message.get("data", {}))
                    session.config = config
                    logger.info(
                        f"Updated config for session {session_id}: {config}"
                    )

                # Xử lý yêu cầu reset
                elif message_type == "reset":
                    # Hủy task hiện tại nếu có
                    if session_id in active_transcription_tasks:
                        active_transcription_tasks[session_id].cancel()
                        await asyncio.sleep(0.1)  # Đợi task dừng

                    # Reset session
                    session.reset_buffers()
                    session.create_recognizer()

                    # Khởi động lại task
                    start_transcription_task(session_id, websocket)

                    await websocket.send_json(
                        {
                            "type": "status",
                            "status": "reset_completed",
                            "timestamp": time.time() * 1000,
                        }
                    )

                return True
            except json.JSONDecodeError:
                logger.warning("Received invalid JSON message")
                return True

        # Xử lý tin nhắn binary (audio data)
        elif "bytes" in data:
            audio_data = data["bytes"]

            # Thêm audio chunk vào session
            session.add_audio_chunk(audio_data)

            # Khởi động task transcription nếu chưa có
            if (
                session_id not in active_transcription_tasks
                or active_transcription_tasks[session_id].done()
            ):
                start_transcription_task(session_id, websocket)

            return True

        return True
    except WebSocketDisconnect:
        return False
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        return True


def start_transcription_task(session_id: str, websocket: WebSocket):
    """
    Khởi động task để xử lý transcription.

    Parameters:
    -----------
    session_id : str
        ID của session
    websocket : WebSocket
        WebSocket connection để gửi kết quả về client
    """
    # Tạo task mới
    task = asyncio.create_task(process_audio_vosk(session_id, websocket))

    # Lưu task
    active_transcription_tasks[session_id] = task


async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    Endpoint WebSocket chính để streaming audio.

    Parameters:
    -----------
    websocket : WebSocket
        WebSocket connection
    session_id : str
        ID của session
    """
    await websocket.accept()

    # Tạo hoặc reset session
    session = session_manager.create_session(session_id)
    active_connections[session_id] = websocket

    logger.info(f"New WebSocket connection: {session_id}")

    try:
        # Thông báo kết nối thành công
        await websocket.send_json(
            {
                "type": "connection_status",
                "status": "connected",
                "session_id": session_id,
                "timestamp": time.time() * 1000,
                "engines_available": {
                    "vosk": VOSK_AVAILABLE,
                    "speech_recognition": SR_AVAILABLE,
                },
            }
        )

        # Loop xử lý tin nhắn
        while True:
            if not await process_client_message(websocket, session_id):
                break
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json(
                {
                    "type": "error",
                    "message": str(e),
                    "timestamp": time.time() * 1000,
                }
            )
        except:
            pass
    finally:
        # Cleanup khi kết thúc
        if session_id in active_connections:
            del active_connections[session_id]

        # Hủy task nếu có
        if session_id in active_transcription_tasks:
            active_transcription_tasks[session_id].cancel()
            del active_transcription_tasks[session_id]


async def cleanup_old_sessions(max_age_minutes: int = 30):
    """
    Dọn dẹp các session cũ.

    Parameters:
    -----------
    max_age_minutes : int
        Thời gian tối đa (phút) mà một session có thể tồn tại không hoạt động
    """
    while True:
        now = time.time()
        to_delete = []

        for session_id, session in session_manager.get_all_sessions().items():
            age = (now - session.last_activity.timestamp()) / 60
            if age > max_age_minutes:
                to_delete.append(session_id)

        for session_id in to_delete:
            logger.info(f"Cleaning up old session: {session_id}")

            # Hủy task nếu có
            if session_id in active_transcription_tasks:
                active_transcription_tasks[session_id].cancel()
                del active_transcription_tasks[session_id]

            # Xóa session
            session_manager.delete_session(session_id)

        # Đợi 1 phút trước khi kiểm tra lại
        await asyncio.sleep(60)
