"""
Các hàm tiện ích để xử lý audio.
"""

from typing import Tuple

import numpy as np

from ..config import logger


def float32_to_int16(audio_data: bytes) -> bytes:
    """
    Chuyển đổi dữ liệu audio từ float32 sang int16.

    Parameters:
    -----------
    audio_data : bytes
        Dữ liệu audio ở định dạng float32

    Returns:
    --------
    bytes
        Dữ liệu audio ở định dạng int16
    """
    try:
        # Chuyển bytes thành float32 numpy array
        float_array = np.frombuffer(audio_data, dtype=np.float32)

        # Chuẩn hóa và chuyển đổi sang int16
        float_array = np.clip(float_array, -1.0, 1.0)
        int16_array = (float_array * 32767).astype(np.int16)

        # Chuyển đổi trở lại thành bytes
        return int16_array.tobytes()
    except Exception as e:
        logger.error(f"Error converting float32 to int16: {e}")
        return audio_data


def int16_to_float32(audio_data: bytes) -> bytes:
    """
    Chuyển đổi dữ liệu audio từ int16 sang float32.

    Parameters:
    -----------
    audio_data : bytes
        Dữ liệu audio ở định dạng int16

    Returns:
    --------
    bytes
        Dữ liệu audio ở định dạng float32
    """
    try:
        # Chuyển bytes thành int16 numpy array
        int_array = np.frombuffer(audio_data, dtype=np.int16)

        # Chuẩn hóa và chuyển đổi sang float32
        float_array = (int_array / 32767).astype(np.float32)

        # Chuyển đổi trở lại thành bytes
        return float_array.tobytes()
    except Exception as e:
        logger.error(f"Error converting int16 to float32: {e}")
        return audio_data


def detect_voice_activity(
    audio_data: bytes, threshold: float = 0.3
) -> Tuple[bool, float]:
    """
    Kiểm tra xem có giọng nói trong audio hay không.

    Parameters:
    -----------
    audio_data : bytes
        Dữ liệu audio cần kiểm tra
    threshold : float
        Ngưỡng để xác định có giọng nói

    Returns:
    --------
    Tuple[bool, float]
        (has_voice, energy) - has_voice: True nếu có giọng nói, False nếu không
                            - energy: mức năng lượng của audio
    """
    try:
        # Chuyển bytes thành float32 numpy array
        float_array = np.frombuffer(audio_data, dtype=np.float32)

        # Tính RMS (Root Mean Square)
        rms = np.sqrt(np.mean(np.square(float_array)))

        # So sánh với ngưỡng
        return rms > threshold, rms
    except Exception as e:
        logger.error(f"Error detecting voice activity: {e}")
        return False, 0.0


def calculate_audio_duration(
    audio_data: bytes, sample_rate: int = 16000, bytes_per_sample: int = 4
) -> float:
    """
    Tính thời lượng của audio.

    Parameters:
    -----------
    audio_data : bytes
        Dữ liệu audio
    sample_rate : int
        Tần số lấy mẫu
    bytes_per_sample : int
        Số byte cho mỗi mẫu (float32 = 4, int16 = 2)

    Returns:
    --------
    float
        Thời lượng audio tính bằng giây
    """
    try:
        # Tính số mẫu
        num_samples = len(audio_data) / bytes_per_sample

        # Tính thời lượng
        duration = num_samples / sample_rate

        return duration
    except Exception as e:
        logger.error(f"Error calculating audio duration: {e}")
        return 0.0
