import speech_recognition as sr

r = sr.Recognizer()

with sr.Microphone() as source:
    print("Listening...")
    audio = r.listen(source, timeout=10, phrase_time_limit=50)

# Calculate duration in seconds:
duration = len(audio.frame_data) / (audio.sample_rate * audio.sample_width)
print("Audio length: {:.2f} seconds".format(duration))


"""try:
    text = r.recognize_vosk(audio, language="en")
    print(text)

except sr.UnknownValueError:
    print("Recognizer Failed..")

except sr.RequestError as e:
    print("Request Failed...", e)


class ModelSpeechToText:
    def __init__(self, audio_path: str, model_path: str) -> None:
        self.audio_path = audio_path
        self.wf = wave.open(self.audio_path)
        self.model = Model(model_path)

    def load_models():
        # Load Wav2Vec2 (Transcriber model)
        stt_model = HubertForCTC.from_pretrained(
            "facebook/hubert-large-ls960-ft"
        )
        stt_tokenizer = Wav2Vec2Processor.from_pretrained(
            "facebook/hubert-large-ls960-ft"
        )

        return stt_tokenizer, stt_model"""
