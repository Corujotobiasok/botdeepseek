import speech_recognition as sr
import pyttsx3
import time
import threading
from queue import Queue

class VoiceEngine:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = 1.2
        self.recognizer.energy_threshold = 3500
        self.recognizer.dynamic_energy_threshold = True

        self.engine = pyttsx3.init()
        self._configure_voice()

        self.speech_queue = Queue()
        self.speaking = False
        self._start_speech_thread()

    def _configure_voice(self):
        voices = self.engine.getProperty('voices')
        for voice in voices:
            if 'spanish' in voice.name.lower():
                self.engine.setProperty('voice', voice.id)
                break
        self.engine.setProperty('rate', 160)
        self.engine.setProperty('volume', 0.9)

    def _start_speech_thread(self):
        def speech_worker():
            while True:
                text = self.speech_queue.get()
                self.speaking = True
                self.engine.say(text)
                self.engine.runAndWait()
                self.speaking = False
                self.speech_queue.task_done()
        thread = threading.Thread(target=speech_worker, daemon=True)
        thread.start()

    def listen(self, timeout=3):
        with sr.Microphone() as source:
            try:
                print(f"Escuchando (timeout: {timeout}s)...")
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=7)
                text = self.recognizer.recognize_google(audio, language="es-AR")
                print(f"Usuario: {text}")
                return text
            except (sr.WaitTimeoutError, sr.UnknownValueError):
                return None
            except Exception as e:
                print(f"Error en reconocimiento: {e}")
                return None

    def speak(self, text, async_mode=True):
        print(f"Jarvis: {text}")
        self.speech_queue.put(text)