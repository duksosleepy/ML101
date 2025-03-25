"""
Factory pattern để tạo và quản lý recognizer.
"""

from ..config import (
    DEFAULT_WHISPER_MODEL_SIZE,
    SR_AVAILABLE,
    VOSK_AVAILABLE,
    WHISPER_AVAILABLE,
    logger,
)
from .base import BaseRecognizer
from .registry import RecognizerRegistry


def create_recognizer(
    engine: str = "auto",
    sample_rate: int = 16000,
    language: str = "vi",
    partial_results: bool = True,
    model_size: str = None,
    **kwargs,
) -> BaseRecognizer | None:
    """
    Tạo recognizer phù hợp dựa trên các cài đặt có sẵn.

    Parameters:
    -----------
    engine : str
        Loại engine muốn sử dụng: "vosk", "whisper", "speechrecognition", "sr", hoặc "auto"
    sample_rate : int
        Tần số lấy mẫu của audio
    language : str
        Mã ngôn ngữ (vi, en, etc.)
    partial_results : bool
        Có trả về kết quả tạm thời không
    model_size : str
        Kích thước mô hình Whisper (tiny, base, small, medium, large)
    **kwargs : dict
        Các tham số bổ sung

    Returns:
    --------
    BaseRecognizer
        Instance của recognizer phù hợp hoặc None nếu không có engine nào khả dụng
    """
    # Cài đặt mặc định cho model_size
    if model_size is None:
        model_size = DEFAULT_WHISPER_MODEL_SIZE

    # Chuẩn hóa tên engine
    engine = engine.lower()
    if engine == "speechrecognition":
        engine = "sr"

    # Chuẩn bị tham số
    params = {
        "sample_rate": sample_rate,
        "language": language,
        "partial_results": partial_results,
        "model_size": model_size,
        **kwargs,
    }

    # Sử dụng Registry để tạo recognizer
    recognizer = RecognizerRegistry.create_recognizer(engine, **params)

    # Log kết quả
    if recognizer:
        logger.info(f"Created {engine} recognizer for language: {language}")
    else:
        logger.warning(f"Failed to create {engine} recognizer")

    return recognizer


# Singleton pattern để tái sử dụng recognizer
_recognizer_instances: dict[str, BaseRecognizer] = {}


def get_or_create_recognizer(
    engine: str = "auto",
    sample_rate: int = 16000,
    language: str = "vi",
    **kwargs,
) -> BaseRecognizer | None:
    """
    Lấy recognizer có sẵn hoặc tạo mới nếu cần.

    Parameters:
    -----------
    engine : str
        Loại engine muốn sử dụng: "vosk", "whisper", "speechrecognition", "sr", hoặc "auto"
    sample_rate : int
        Tần số lấy mẫu của audio
    language : str
        Mã ngôn ngữ (vi, en, etc.)
    **kwargs : dict
        Các tham số bổ sung

    Returns:
    --------
    BaseRecognizer
        Instance của recognizer phù hợp hoặc None nếu không có engine nào khả dụng
    """
    key = f"{engine}_{language}_{sample_rate}"

    # Chuẩn hóa thành lowercase
    key = key.lower()

    # Thêm model_size vào key nếu là Whisper
    if engine.lower() in ["whisper", "auto"] and "model_size" in kwargs:
        key += f"_{kwargs['model_size']}"

    if key not in _recognizer_instances:
        _recognizer_instances[key] = create_recognizer(
            engine, sample_rate, language, **kwargs
        )

    return _recognizer_instances[key]


def get_available_engines() -> dict[str, bool]:
    """
    Lấy thông tin về các engine có sẵn.

    Returns:
    --------
    Dict[str, bool]
        Dictionary với key là tên engine và value là trạng thái khả dụng
    """
    return {
        "whisper": WHISPER_AVAILABLE,
        "vosk": VOSK_AVAILABLE,
        "sr": SR_AVAILABLE,
    }
