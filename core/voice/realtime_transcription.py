"""
Ứng dụng chuyển đổi giọng nói thành văn bản theo thời gian thực từ microphone.

Sử dụng:
    python realtime_transcription.py [--engine vosk|whisper|sr] [--language vi|en] [--sample-rate 16000]
"""

import argparse
import signal
import sys
import time

# Import các module đã tạo
from config import logger
from microphone import AudioInputRegistry, create_audio_input
from models.schemas import TranscriptionConfig
from recognition import RecognizerRegistry, create_recognizer


class RealtimeTranscription:
    """
    Lớp quản lý quá trình chuyển đổi giọng nói thành văn bản theo thời gian thực.
    """

    def __init__(
        self,
        audio_engine: str = "auto",
        recognition_engine: str = "auto",
        language: str = "vi",
        sample_rate: int = 16000,
        device_index: int | None = None,
        partial_results: bool = True,
        vad_enabled: bool = True,
        vad_threshold: float = 0.3,
        silence_duration: float = 0.5,
        model_size: str = "small",
    ):
        self.audio_engine = audio_engine
        self.recognition_engine = recognition_engine
        self.language = language
        self.sample_rate = sample_rate
        self.device_index = device_index
        self.model_size = model_size

        # Cấu hình transcription
        self.config = TranscriptionConfig(
            engine=recognition_engine,
            model_size=model_size,
            partial_results=partial_results,
            vad_enabled=vad_enabled,
            vad_threshold=vad_threshold,
            silence_duration=silence_duration,
        )

        # Trạng thái
        self.running = False
        self.is_speaking = False
        self.silence_start = None

        # Kết quả transcription
        self.current_text = ""
        self.partial_text = ""
        self.transcript_history = []

        # Khởi tạo các thành phần
        self._init_components()

    def _init_components(self):
        """
        Khởi tạo các thành phần cần thiết.
        """
        # Khởi tạo recognizer
        self.recognizer = create_recognizer(
            engine=self.recognition_engine,
            sample_rate=self.sample_rate,
            language=self.language,
            partial_results=self.config.partial_results,
            model_size=self.model_size,
        )

        if not self.recognizer:
            logger.error(
                "Failed to create speech recognizer. "
                "Make sure you have installed Vosk, Whisper or SpeechRecognition."
            )
            return

        # Khởi tạo audio input
        self.audio_input = create_audio_input(
            engine=self.audio_engine,
            sample_rate=self.sample_rate,
            channels=1,
            device_index=self.device_index,
        )

        if not self.audio_input:
            logger.error(
                "Failed to create audio input. "
                "Make sure you have installed PyAudio or SpeechRecognition."
            )
            return

        # Thêm callback để xử lý audio data
        self.audio_input.add_callback(self._process_audio)

    def _process_audio(self, audio_data: bytes):
        """
        Xử lý audio data và thực hiện transcription.
        """
        if not self.recognizer:
            return

        try:
            # Xử lý audio bằng recognizer
            result = self.recognizer.process_audio(audio_data)

            if result["text"]:
                text = result["text"]
                is_final = result["is_final"]

                if is_final:
                    # Kết quả hoàn chỉnh
                    self.current_text = text
                    self.partial_text = ""
                    self.transcript_history.append(text)

                    # In ra màn hình
                    print(f"\n[Final] {text}")

                else:
                    # Kết quả tạm thời
                    self.partial_text = text

                    # In ra màn hình
                    print(f"\r[Partial] {text}", end="", flush=True)

        except Exception as e:
            logger.error(f"Error processing audio data: {e}")

    def start(self):
        """
        Bắt đầu quá trình chuyển đổi giọng nói thành văn bản.
        """
        if self.running:
            logger.warning("Transcription is already running")
            return

        if not self.audio_input or not self.recognizer:
            logger.error(
                "Cannot start transcription: audio input or recognizer not available"
            )
            return

        try:
            print("\nStarting real-time transcription...")
            print(f"Using recognition engine: {self.recognition_engine}")
            if self.recognition_engine == "whisper":
                print(f"Whisper model size: {self.model_size}")
            print(f"Using audio input: {self.audio_input.__class__.__name__}")
            print(f"Language: {self.language}")
            print("Speak into your microphone. Press Ctrl+C to stop.\n")

            # Khởi động audio input
            self.running = True
            self.audio_input.start()

            # Chờ cho đến khi bị ngắt bởi Ctrl+C
            try:
                while self.running:
                    time.sleep(0.1)
            except KeyboardInterrupt:
                print("\nTranscription stopped by user")

        except Exception as e:
            logger.error(f"Error starting transcription: {e}")
        finally:
            self.stop()

    def stop(self):
        """
        Dừng quá trình chuyển đổi giọng nói thành văn bản.
        """
        self.running = False

        # Dừng audio input
        if self.audio_input:
            self.audio_input.stop()

        print("\nTranscription stopped")

        # In ra bản ghi hoàn chỉnh
        if self.transcript_history:
            print("\nTranscript history:")
            for i, text in enumerate(self.transcript_history, 1):
                print(f"{i}. {text}")

    def list_devices(self):
        """
        Liệt kê các thiết bị âm thanh có sẵn.
        """
        if not self.audio_input:
            print("Audio input not available")
            return

        devices = self.audio_input.get_device_list()

        if not devices:
            print("No audio devices found")
            return

        print("\nAvailable audio input devices:")
        for device in devices:
            print(f"Index: {device['index']}, Name: {device['name']}")


def main():
    """
    Hàm main để chạy ứng dụng từ command line.
    """
    # Xử lý tham số dòng lệnh
    parser = argparse.ArgumentParser(description="Real-time Speech to Text")
    parser.add_argument(
        "--audio-engine",
        choices=["pyaudio", "sr", "auto"],
        default="auto",
        help="Audio input engine to use (default: auto)",
    )
    parser.add_argument(
        "--engine",
        choices=["vosk", "whisper", "sr", "auto"],
        default="auto",
        help="Recognition engine to use (default: auto)",
    )
    parser.add_argument(
        "--language",
        choices=["vi", "en"],
        default="vi",
        help="Language for speech recognition (default: vi)",
    )
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=16000,
        help="Audio sample rate in Hz (default: 16000)",
    )
    parser.add_argument(
        "--device-index",
        type=int,
        default=None,
        help="Index of audio input device to use (default: system default)",
    )
    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="List available audio input devices and exit",
    )
    parser.add_argument(
        "--model-size",
        choices=["tiny", "base", "small", "medium", "large", "large-v2"],
        default="small",
        help="Model size for Whisper (default: small)",
    )

    args = parser.parse_args()

    # Hiển thị thông tin về các engine có sẵn
    print("\nAvailable recognition engines:")
    for engine in RecognizerRegistry.get_available_engines():
        print(f"- {engine}: Available")

    print("\nAvailable audio engines:")
    for engine in AudioInputRegistry.get_available_engines():
        print(f"- {engine}: Available")

    # Tạo đối tượng transcription
    transcription = RealtimeTranscription(
        audio_engine=args.audio_engine,
        recognition_engine=args.engine,
        language=args.language,
        sample_rate=args.sample_rate,
        device_index=args.device_index,
        model_size=args.model_size,
    )

    # Liệt kê thiết bị nếu yêu cầu
    if args.list_devices:
        transcription.list_devices()
        return

    # Thiết lập xử lý tín hiệu để thoát nhẹ nhàng khi Ctrl+C
    def signal_handler(sig, frame):
        print("\nReceived interrupt signal, stopping...")
        transcription.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    # Bắt đầu transcription
    transcription.start()


if __name__ == "__main__":
    main()
