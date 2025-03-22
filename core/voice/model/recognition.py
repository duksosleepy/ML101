from typing import Protocol

from transformers import HubertForCTC, Wav2Vec2Processor
from vosk import Model


class BaseModel(Protocol):
    def __init__(self, audio_path: str, model_path: str) -> None: ...

    def load_model(self) -> None: ...


class VoskSpeechToText:
    def __init__(self, audio_path: str, model_path: str) -> None:
        self.model = Model(model_path)
        self.model_path = model_path

    def load_models(self):
        stt_model = HubertForCTC.from_pretrained(self.model_path)
        stt_tokenizer = Wav2Vec2Processor.from_pretrained(self.model_path)

        return stt_tokenizer, stt_model


class WhisperSpeechToText:
    def __init__(self, audio_path: str, model_path: str) -> None:
        self.model = Model(model_path)
        self.model_path = model_path

    def load_models(self):
        stt_model = HubertForCTC.from_pretrained(self.model_path)
        stt_tokenizer = Wav2Vec2Processor.from_pretrained(self.model_path)

        return stt_tokenizer, stt_model
