# Load the Vosk model
import json

import pyaudio
import speech_recognition as sr
from vosk import KaldiRecognizer

from core.voice.model.recognition import (
    Model,
)


class VoskRecognizer:
    def __init__(self, model: Model):
        self.recognizer = KaldiRecognizer(model, sample_rate=16000)
        self.microphone = pyaudio.PyAudio()

    def streaming(self):
        stream = self.microphone.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=8192,
        )
        stream.start_stream()
        data = stream.read(4096, exception_on_overflow=False)
        if self.recognizer.AcceptWaveform(data):
            result = json.loads(self.recognizer.Result())
            print("You:", result["text"])


class SRRecognizer:
    def __init__(self):
        self.r = sr.Recognizer()

    def streaming(self):
        with sr.Microphone() as source:
            print("Listening...")
            audio = self.r.listen(source, timeout=10, phrase_time_limit=50)

        try:
            text = self.r.recognize_vosk(audio, language="en")
            print(text)
        except sr.UnknownValueError:
            print("Recognizer Failed..")
        except sr.RequestError as e:
            print("Request Failed...", e)
