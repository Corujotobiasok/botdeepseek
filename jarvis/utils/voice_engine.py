import speech_recognition as sr
import pyttsx3
import time
import threading
from queue import Queue

class VoiceEngine:
    def __init__(self):
        # Configuración de reconocimiento
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = 1.2  # Más sensible para respuestas rápidas
        self.recognizer.energy_threshold = 3500
        self.recognizer.dynamic_energy_threshold = True
        
        # Configuración de voz
        self.engine = pyttsx3.init()
        self._configure_voice()
        
        # Cola para manejar habla asíncrona
        self.speech_queue = Queue()
        self.speaking = False
        self._start_speech_thread()

    def _configure_voice(self):
        """Configura la voz con acento argentino"""
        voices = self.engine.getProperty('voices')
        for voice in voices:
            if 'spanish' in voice.languages or 'es' in voice.languages:
                self.engine.setProperty('voice', voice.id)
                break
        
        # Ajustes para sonido más natural
        self.engine.setProperty('rate', 160)  # Un poco más rápido
        self.engine.setProperty('volume', 0.9)
        self.engine.setProperty('pitch', 110)  # Tono ligeramente más alto

    def _start_speech_thread(self):
        """Inicia hilo para manejar cola de habla"""
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
        """Escucha con timeout configurable"""
        with sr.Microphone() as source:
            try:
                print(f"Escuchando (timeout: {timeout}s)...")
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=7)
                text = self.recognizer.recognize_google(audio, language="es-AR")
                print(f"Usuario: {text}")
                return text
            except sr.WaitTimeoutError:
                return None
            except sr.UnknownValueError:
                print("No se pudo entender el audio")
                return None
            except Exception as e:
                print(f"Error en reconocimiento: {e}")
                return None

    def speak(self, text, async_mode=True):
        """Habla texto, con opción para modo asíncrono"""
        print(f"Jarvis: {text}")
        if async_mode and self.speaking:
            self.speech_queue.put(text)  # Agrega a cola si ya está hablando
        else:
            self.speech_queue.put(text)