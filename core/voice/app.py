"""
Khởi tạo ứng dụng FastAPI.
"""

import asyncio

from config import logger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import api_router, cleanup_old_sessions, websocket_endpoint

# Tạo ứng dụng FastAPI
app = FastAPI(
    title="Realtime Audio Streaming API",
    description="API để streaming audio và nhận dạng giọng nói theo thời gian thực",
    version="1.0.0",
)

# Thêm CORS middleware để cho phép kết nối từ frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Có thể hạn chế lại trong môi trường production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Thêm các API route
app.include_router(api_router)

# Thêm WebSocket endpoint
app.add_websocket_route("/audio/{session_id}/stream", websocket_endpoint)


# Khởi động background task để dọn dẹp session cũ
@app.on_event("startup")
async def startup_event():
    """
    Khởi động các background task khi server khởi động.
    """
    # Khởi động task dọn dẹp session cũ
    asyncio.create_task(cleanup_old_sessions())
    logger.info("Started session cleanup task")

    # Thông báo server đã khởi động
    logger.info("Server started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Dọn dẹp khi server shutdown.
    """
    logger.info("Server shutting down")
