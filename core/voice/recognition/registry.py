"""
Registry cho các speech recognizer.
"""

from collections.abc import Callable

from ..config import logger
from .base import BaseRecognizer


class RecognizerRegistry:
    """
    Registry cho các speech recognizer.
    Quản lý việc đăng ký và tạo các recognizer khác nhau.
    """

    # Dictionary để lưu trữ các lớp recognizer
    _recognizers: dict[str, type[BaseRecognizer]] = {}

    # Dictionary để lưu trữ các điều kiện khả dụng
    _availability_conditions: dict[str, Callable[[], bool]] = {}

    @classmethod
    def register(
        cls,
        engine_name: str,
        recognizer_class: type[BaseRecognizer],
        availability_condition: Callable[[], bool] | None = None,
    ):
        """
        Đăng ký một lớp recognizer với registry.

        Parameters:
        -----------
        engine_name : str
            Tên của engine
        recognizer_class : Type[BaseRecognizer]
            Lớp recognizer cần đăng ký
        availability_condition : Optional[Callable[[], bool]]
            Hàm kiểm tra tính khả dụng của engine
        """
        cls._recognizers[engine_name] = recognizer_class

        if availability_condition is not None:
            cls._availability_conditions[engine_name] = availability_condition

        logger.debug(f"Registered recognizer: {engine_name}")

    @classmethod
    def create_recognizer(cls, engine_name: str, **kwargs) -> BaseRecognizer | None:
        """
        Tạo một instance của recognizer theo tên.

        Parameters:
        -----------
        engine_name : str
            Tên của engine
        **kwargs : dict
            Các tham số cho constructor của recognizer

        Returns:
        --------
        Optional[BaseRecognizer]
            Instance của recognizer hoặc None nếu không tìm thấy
        """
        # Trường hợp "auto" - chọn engine đầu tiên có sẵn
        if engine_name.lower() == "auto":
            return cls.create_auto_recognizer(**kwargs)

        # Trường hợp yêu cầu engine cụ thể
        if engine_name not in cls._recognizers:
            logger.warning(f"Engine not found: {engine_name}")
            return None

        recognizer_class = cls._recognizers[engine_name]

        # Kiểm tra điều kiện khả dụng nếu có
        if engine_name in cls._availability_conditions:
            condition = cls._availability_conditions[engine_name]
            if not condition():
                logger.warning(f"Engine {engine_name} is not available")
                return None

        try:
            recognizer = recognizer_class(**kwargs)

            # Kiểm tra xem recognizer có thực sự khả dụng không
            if recognizer.is_available():
                logger.info(f"Created recognizer: {engine_name}")
                return recognizer
            logger.warning(f"Created recognizer {engine_name} but it's not available")
            return None

        except Exception as e:
            logger.error(f"Error creating recognizer {engine_name}: {e}")
            return None

    @classmethod
    def create_auto_recognizer(cls, **kwargs) -> BaseRecognizer | None:
        """
        Tự động chọn và tạo recognizer phù hợp nhất dựa trên tính khả dụng.

        Parameters:
        -----------
        **kwargs : dict
            Các tham số cho constructor của recognizer

        Returns:
        --------
        Optional[BaseRecognizer]
            Instance của recognizer hoặc None nếu không có engine nào khả dụng
        """
        # Thứ tự ưu tiên: whisper > vosk > sr
        priority_order = ["whisper", "vosk", "sr"]

        for engine_name in priority_order:
            if engine_name in cls._recognizers:
                # Kiểm tra điều kiện khả dụng nếu có
                if engine_name in cls._availability_conditions:
                    condition = cls._availability_conditions[engine_name]
                    if not condition():
                        logger.debug(
                            f"Engine {engine_name} is not available, trying next"
                        )
                        continue

                # Thử tạo recognizer
                try:
                    recognizer = cls._recognizers[engine_name](**kwargs)
                    if recognizer.is_available():
                        logger.info(f"Auto-selected recognizer: {engine_name}")
                        return recognizer
                except Exception as e:
                    logger.debug(f"Error creating recognizer {engine_name}: {e}")

        logger.warning("No suitable recognizer found")
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

        for engine_name in cls._recognizers:
            # Kiểm tra điều kiện khả dụng nếu có
            if engine_name in cls._availability_conditions:
                condition = cls._availability_conditions[engine_name]
                if not condition():
                    continue

            # Thử tạo một recognizer để kiểm tra
            try:
                recognizer = cls._recognizers[engine_name]()
                if recognizer.is_available():
                    available_engines.append(engine_name)
            except Exception:
                pass

        return available_engines
