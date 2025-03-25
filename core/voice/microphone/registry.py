"""
Registry cho các audio input processor.
"""

from collections.abc import Callable

from ..config import logger
from .base import BaseAudioInput


class AudioInputRegistry:
    """
    Registry cho các audio input processor.
    Quản lý việc đăng ký và tạo các audio input khác nhau.
    """

    # Dictionary để lưu trữ các lớp audio input
    _inputs: dict[str, type[BaseAudioInput]] = {}

    # Dictionary để lưu trữ các điều kiện khả dụng
    _availability_conditions: dict[str, Callable[[], bool]] = {}

    @classmethod
    def register(
        cls,
        engine_name: str,
        input_class: type[BaseAudioInput],
        availability_condition: Callable[[], bool] | None = None,
    ):
        """
        Đăng ký một lớp audio input với registry.

        Parameters:
        -----------
        engine_name : str
            Tên của engine
        input_class : Type[BaseAudioInput]
            Lớp audio input cần đăng ký
        availability_condition : Optional[Callable[[], bool]]
            Hàm kiểm tra tính khả dụng của engine
        """
        cls._inputs[engine_name] = input_class

        if availability_condition is not None:
            cls._availability_conditions[engine_name] = availability_condition

        logger.debug(f"Registered audio input: {engine_name}")

    @classmethod
    def create_audio_input(cls, engine_name: str, **kwargs) -> BaseAudioInput | None:
        """
        Tạo một instance của audio input theo tên.

        Parameters:
        -----------
        engine_name : str
            Tên của engine
        **kwargs : dict
            Các tham số cho constructor của audio input

        Returns:
        --------
        Optional[BaseAudioInput]
            Instance của audio input hoặc None nếu không tìm thấy
        """
        # Trường hợp "auto" - chọn engine đầu tiên có sẵn
        if engine_name.lower() == "auto":
            return cls.create_auto_audio_input(**kwargs)

        # Trường hợp yêu cầu engine cụ thể
        if engine_name not in cls._inputs:
            logger.warning(f"Audio input engine not found: {engine_name}")
            return None

        input_class = cls._inputs[engine_name]

        # Kiểm tra điều kiện khả dụng nếu có
        if engine_name in cls._availability_conditions:
            condition = cls._availability_conditions[engine_name]
            if not condition():
                logger.warning(f"Audio input engine {engine_name} is not available")
                return None

        try:
            audio_input = input_class(**kwargs)

            # Kiểm tra xem audio input có thực sự khả dụng không
            if audio_input.is_available():
                logger.info(f"Created audio input: {engine_name}")
                return audio_input
            logger.warning(f"Created audio input {engine_name} but it's not available")
            return None

        except Exception as e:
            logger.error(f"Error creating audio input {engine_name}: {e}")
            return None

    @classmethod
    def create_auto_audio_input(cls, **kwargs) -> BaseAudioInput | None:
        """
        Tự động chọn và tạo audio input phù hợp nhất dựa trên tính khả dụng.

        Parameters:
        -----------
        **kwargs : dict
            Các tham số cho constructor của audio input

        Returns:
        --------
        Optional[BaseAudioInput]
            Instance của audio input hoặc None nếu không có engine nào khả dụng
        """
        # Thứ tự ưu tiên: pyaudio > sr
        priority_order = ["pyaudio", "sr"]

        for engine_name in priority_order:
            if engine_name in cls._inputs:
                # Kiểm tra điều kiện khả dụng nếu có
                if engine_name in cls._availability_conditions:
                    condition = cls._availability_conditions[engine_name]
                    if not condition():
                        logger.debug(
                            f"Audio input engine {engine_name} is not available, trying next"
                        )
                        continue

                # Thử tạo audio input
                try:
                    audio_input = cls._inputs[engine_name](**kwargs)
                    if audio_input.is_available():
                        logger.info(f"Auto-selected audio input: {engine_name}")
                        return audio_input
                except Exception as e:
                    logger.debug(f"Error creating audio input {engine_name}: {e}")

        logger.warning("No suitable audio input found")
        return None

    @classmethod
    def get_available_engines(cls) -> list[str]:
        """
        Lấy danh sách các engine có sẵn.

        Returns:
        --------
        List[str]
            Danh sách tên các engine có sẵn
        """
        available_engines = []

        for engine_name in cls._inputs:
            # Kiểm tra điều kiện khả dụng nếu có
            if engine_name in cls._availability_conditions:
                condition = cls._availability_conditions[engine_name]
                if not condition():
                    continue

            # Thử tạo một audio input để kiểm tra
            try:
                audio_input = cls._inputs[engine_name]()
                if audio_input.is_available():
                    available_engines.append(engine_name)
            except Exception:
                pass

        return available_engines
