| Layer | Tech |
| :------| :-----------|
| Frontend   | [Reflex](https://reflex.dev/) |
| Backend | [FastAPI](https://fastapi.tiangolo.com/) |
| APIendpoint Serialization/Deserialization | [Cattrs](https://cattrs.readthedocs.io/)/[Attrs](https://www.attrs.org/) + [Marshmallow](https://marshmallow.readthedocs.io/) + [APIspec](https://apispec.readthedocs.io/) |
| LLM Engine |  |
| &nbsp;&nbsp;&nbsp;&nbsp;Speech Recognition | [Vosk](https://alphacephei.com/vosk/) + [speech_recognition](https://pypi.org/project/SpeechRecognition/)  |




-----------------------------------------------------------------

# Realtime Speech Recognition API

Dự án mã nguồn mở cho phép nhận dạng giọng nói theo thời gian thực bằng tiếng Việt và tiếng Anh, hỗ trợ cả API trực tuyến và ứng dụng offline.

## Tính năng chính

- **Nhận dạng theo thời gian thực**: Hiển thị từng từ ngay khi được nhận diện
- **Đa dạng nguồn âm thanh**: Hỗ trợ cả WebSocket (qua trình duyệt) và trực tiếp từ microphone
- **Hỗ trợ đa ngôn ngữ**: Tiếng Việt, tiếng Anh và có thể mở rộng thêm
- **Nhiều engine nhận dạng**:
  - **OpenAI Whisper**: Độ chính xác cao, hỗ trợ nhiều ngôn ngữ, cần GPU để tốc độ tốt nhất
  - **Vosk**: Nhận dạng offline, nhanh, ít tài nguyên
  - **SpeechRecognition**: Engine dự phòng với nhiều nhà cung cấp
- **Phát hiện giọng nói**: Tự động nhận biết khi nào người dùng bắt đầu và ngừng nói
- **Xử lý file**: Hỗ trợ transcribe file audio đã tải lên
- **Tính mở rộng cao**: Cấu trúc module dễ bảo trì và mở rộng

## Cài đặt

### Yêu cầu hệ thống

- Python 3.8+
- Các thư viện Python được liệt kê trong requirements.txt
- (Tùy chọn) GPU với CUDA để tăng tốc Whisper

### Bước 1: Cài đặt các gói cần thiết

```bash
# Cài đặt các gói cần thiết cho API
pip install fastapi uvicorn numpy pydantic python-multipart

# Cài đặt Vosk cho nhận dạng offline
pip install vosk

# Cài đặt Whisper cho chất lượng cao hơn
pip install openai-whisper

# Cài đặt PyTorch (GPU nếu có thể)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Tùy chọn: cài đặt PyAudio và SpeechRecognition cho thu âm trực tiếp
pip install pyaudio SpeechRecognition
```

### Bước 2: Tải các mô hình nhận dạng tiếng nói

```bash
# Tạo thư mục cho mô hình Vosk
mkdir -p models/vosk_models

# Tải mô hình tiếng Việt Vosk
wget https://alphacephei.com/vosk/models/vosk-model-vi-0.4.zip
unzip vosk-model-vi-0.4.zip -d models/vosk_models/vosk-model-vi

# Tải mô hình tiếng Anh nhỏ
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip -d models/vosk_models/
```

Whisper sẽ tự động tải mô hình khi cần thiết.

## Sử dụng

### Phương thức 1: API WebSocket (cho ứng dụng web)

1. Khởi động server:

```bash
python main.py
```

2. Kết nối từ frontend qua WebSocket:

```javascript
// Frontend JavaScript
const ws = new WebSocket('ws://localhost:8000/audio/session-id/stream');

// Gửi cấu hình
ws.onopen = () => {
    ws.send(JSON.stringify({
        type: 'config',
        data: {
            engine: 'whisper',      // whisper, vosk, auto
            model_size: 'small',    // tiny, base, small, medium, large (for Whisper)
            partial_results: true,
            vad_enabled: true
        }
    }));
};

// Khi nhận được kết quả từ server
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'transcript') {
        console.log(data.text, data.is_final);
    }
};

// Gửi dữ liệu audio
navigator.mediaDevices.getUserMedia({ audio: true })
    .then((stream) => {
        // Xử lý stream và gửi qua WebSocket
        // ...
    });
```

### Phương thức 2: Transcribe File Audio

```bash
# Gửi yêu cầu POST với curl
curl -X POST "http://localhost:8000/transcribe" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@/path/to/audio.mp3" \
     -F "language=vi" \
     -F "engine=whisper" \
     -F "model_size=small"
```

### Phương thức 3: Ứng dụng độc lập (sử dụng microphone)

Chạy ứng dụng trực tiếp với microphone:

```bash
# Chạy với cài đặt mặc định (tiếng Việt)
python realtime_transcription.py

# Sử dụng Whisper
python realtime_transcription.py --engine whisper

# Chọn model Whisper cụ thể
python realtime_transcription.py --engine whisper --model-size medium

# Chọn ngôn ngữ tiếng Anh
python realtime_transcription.py --language en

# Chọn engine cụ thể
python realtime_transcription.py --engine vosk --audio-engine pyaudio

# Liệt kê thiết bị âm thanh khả dụng
python realtime_transcription.py --list-devices

# Chọn thiết bị âm thanh cụ thể
python realtime_transcription.py --device-index 1
```

## Ví dụ mã nguồn

### Sử dụng trực tiếp từ mã nguồn

```python
from realtime_transcription import RealtimeTranscription

# Tạo đối tượng transcription với Whisper
transcription = RealtimeTranscription(
    audio_engine="pyaudio",
    recognition_engine="whisper",
    language="vi",
    sample_rate=16000,
    model_size="small"  # tiny, base, small, medium, large
)

# Liệt kê thiết bị
transcription.list_devices()

# Bắt đầu nhận dạng
transcription.start()

# Dừng nhận dạng
transcription.stop()
```

## So sánh các Engine

| Engine | Độ chính xác | Tốc độ | Tài nguyên | Offline | Partial results |
|--------|--------------|--------|------------|---------|-----------------|
| Whisper| Cao          | Trung bình | Cao (GPU) | Có      | Không           |
| Vosk   | Trung bình   | Nhanh  | Thấp      | Có      | Có              |
| SpeechRecognition | Tùy thuộc provider | Chậm | Thấp | Không | Không |

## Cấu trúc dự án

```
audio_streaming_api/
├── app.py                  # Khởi tạo ứng dụng FastAPI
├── config.py               # Cấu hình chung
├── main.py                 # Điểm bắt đầu để chạy API server
├── models/                 # Mô hình dữ liệu
│   ├── audio_session.py    # Model AudioSession
│   └── schemas.py          # Pydantic schemas
├── recognition/            # Xử lý nhận dạng giọng nói
│   ├── base.py             # Lớp cơ sở cho recognizer
│   ├── vosk_recognizer.py  # Vosk implementation
│   ├── whisper_recognizer.py # Whisper implementation
│   ├── sr_recognizer.py    # SpeechRecognition implementation
│   └── factory.py          # Factory pattern để tạo recognizer
├── microphone/             # Xử lý thu âm từ microphone
│   ├── base.py             # Lớp cơ sở cho audio input
│   ├── pyaudio_input.py    # PyAudio implementation
│   ├── sr_input.py         # SpeechRecognition implementation
│   └── factory.py          # Factory pattern để tạo audio input
├── routes/                 # Các API endpoint
│   ├── websocket.py        # WebSocket endpoints
│   └── api.py              # REST API endpoints
├── utils/                  # Tiện ích
│   └── audio_processing.py # Các hàm xử lý audio
└── realtime_transcription.py  # Ứng dụng độc lập
```

## Giấy phép

MIT License
