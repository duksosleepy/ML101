"""
Factory pattern để tạo audio input processor.
"""

from typing import Dict, Optional

from ..config import PYAUDIO_AVAILABLE, SR_AVAILABLE, logger
from .base import BaseAudioInput
from .registry import AudioInputRegistry


def create_audio_input(
    engine: str = "auto",
    sample_rate: int = 16000,
    channels: int = 1,
    device_index: Optional[int] = None,
    **kwargs,
) -> Optional[BaseAudioInput]:
    """
    Tạo audio input processor phù hợp dựa trên các cài đặt có sẵn.

    Parameters:
    -----------
    engine : str
        Loại engine muốn sử dụng: "pyaudio", "speechrecognition", "sr", hoặc "auto"
    sample_rate : int
        Tần số lấy mẫu của audio
    channels : int
        Số kênh audio (thường là 1 cho mono, 2 cho stereo)
    device_index : Optional[int]
        Chỉ mục của thiết bị âm thanh muốn sử dụng, hoặc None để sử dụng mặc định
    **kwargs : dict
        Các tham số bổ sung cho audio input engine

    Returns:
    --------
    BaseAudioInput
        Instance của audio input processor phù hợp hoặc None nếu không có engine nào khả dụng
    """
    # Chuẩn hóa tên engine
    engine = engine.lower()
    if engine == "speechrecognition":
        engine = "sr"

    # Chuẩn bị tham số
    params = {
        "sample_rate": sample_rate,
        "channels": channels,
        "device_index": device_index,
        **kwargs,
    }

    # Sử dụng Registry để tạo audio input
    audio_input = AudioInputRegistry.create_audio_input(engine, **params)

    # Log kết quả
    if audio_input:
        logger.info(f"Created {engine} audio input")
    else:
        logger.warning(f"Failed to create {engine} audio input")

    return audio_input


# Singleton pattern để tái sử dụng audio input
_audio_input_instances: Dict[str, BaseAudioInput] = {}


def get_or_create_audio_input(
    engine: str = "auto",
    sample_rate: int = 16000,
    channels: int = 1,
    device_index: Optional[int] = None,
    **kwargs,
) -> Optional[BaseAudioInput]:
    """
    Lấy audio input có sẵn hoặc tạo mới nếu cần.

    Parameters:
    -----------
    engine : str
        Loại engine muốn sử dụng: "pyaudio", "speechrecognition", "sr", hoặc "auto"
    sample_rate : int
        Tần số lấy mẫu của audio
    channels : int
        Số kênh audio
    device_index : Optional[int]
        Chỉ mục của thiết bị âm thanh
    **kwargs : dict
        Các tham số bổ sung

    Returns:
    --------
    BaseAudioInput
        Instance của audio input phù hợp
        hoặc None nếu không có engine nào khả dụng
    """
    device_id_str = str(device_index) if device_index is not None else "default"
    key = f"{engine}_{sample_rate}_{channels}_{device_id_str}"

    if key not in _audio_input_instances:
        _audio_input_instances[key] = create_audio_input(
            engine, sample_rate, channels, device_index, **kwargs
        )

    return _audio_input_instances[key]


def get_available_engines() -> Dict[str, bool]:
    """
    Lấy thông tin về các engine có sẵn.

    Returns:
    --------
    Dict[str, bool]
        Dictionary với key là tên engine và value là trạng thái khả dụng
    """
    return {"pyaudio": PYAUDIO_AVAILABLE, "sr": SR_AVAILABLE}
