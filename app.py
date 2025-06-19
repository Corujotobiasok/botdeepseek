import time
import threading
import json
from datetime import datetime
import requests
from utils.voice_engine import VoiceEngine
from utils.web_controller import WebController
from utils.learning_engine import LearningEngine
from utils.response_manager import ResponseManager


class Jarvis:
    def __init__(self):
        # Cargar configuración
        with open('config.json') as config_file:
            self.config = json.load(config_file)

        self.name = "Jarvis"
        self.activation_word = self.config.get("activation_word", "jarvis")
        self.user_name = self.config.get("user_name", "Señor")
        self.is_active = False
        self.last_activation = 0
        self.response_delay = self.config.get("response_delay", 1.5)

        # Inicializar módulos
        self.voice = VoiceEngine()
        self.web = WebController()
        self.learning = LearningEngine()
        self.response_manager = ResponseManager()
        self.model = self._load_ai_model()

        # Estado de la conversación
        self.current_task = None
        self.is_processing = False
        self.last_interaction = time.time()

        print(f"{self.name} inicializado. Di '{self.activation_word}' para activarme.")

    def _load_ai_model(self):
        """Carga proxy para usar el modelo Gemma a través de Ollama"""
        def generate(prompt):
            try:
                response = requests.post("http://localhost:11434/api/generate", json={
                    "model": "gemma:2b",
                    "prompt": prompt,
                    "stream": False
                }, timeout=15)
                return response.json().get("response", "")
            except Exception as e:
                print(f"Error al generar respuesta: {e}")
                return "No pude generar una respuesta en este momento."
        return type("GemmaModel", (), {"generate": staticmethod(generate)})

    def listen_loop(self):
        while True:
            if not self.is_active and time.time() - self.last_interaction > 300:
                time.sleep(0.5)
                continue

            print("\nEscuchando... (Modo activo)" if self.is_active else "\nEscuchando... (Modo espera)")
            text = self.voice.listen(timeout=3 if self.is_active else 1)

            if text and self.activation_word in text.lower():
                self._activate_assistant()
                continue

            if self.is_active and text:
                self._process_user_command(text)

    def _activate_assistant(self):
        self.is_active = True
        self.last_activation = time.time()
        self.voice.speak(f"¿En qué puedo ayudarte, {self.user_name}?")
        self.last_interaction = time.time()

    def _process_user_command(self, text):
        self.last_interaction = time.time()
        self.voice.speak(self.response_manager.get_acknowledgement())

        processing_thread = threading.Thread(
            target=self._handle_command_processing,
            args=(text,)
        )
        processing_thread.start()
        self._provide_processing_feedback(text)
        processing_thread.join()

    def _handle_command_processing(self, text):
        self.is_processing = True
        try:
            quick_action_response = self._check_quick_actions(text)
            if quick_action_response:
                self.voice.speak(quick_action_response)
                return

            start_time = time.time()
            cached_response = self.learning.get_personalized_response(text)
            if cached_response:
                self.voice.speak(cached_response)
                return

            if time.time() - start_time > 1.5:
                self.voice.speak("Estoy analizando tu solicitud...")

            full_response = self._generate_ai_response(text)

            action_result = self._execute_associated_actions(text, full_response)
            final_response = action_result if action_result else full_response
            self.voice.speak(final_response)

            self.learning.log_interaction(
                command=text,
                response=final_response,
                success=True
            )
        except Exception as e:
            error_msg = f"Disculpa {self.user_name}, hubo un error al procesar tu solicitud."
            self.voice.speak(error_msg)
            self.learning.log_interaction(text, error_msg, False)
        finally:
            self.is_processing = False
            self._deactivate_if_inactive()

    def _provide_processing_feedback(self, text):
        time.sleep(0.3)
        feedback_given = False
        while self.is_processing:
            if time.time() - self.last_interaction > 3 and not feedback_given:
                if "buscar" in text.lower() or "información" in text.lower():
                    self.voice.speak("Estoy buscando la información...")
                else:
                    self.voice.speak("Déjame pensar un momento...")
                feedback_given = True
            time.sleep(0.1)

    def _check_quick_actions(self, text):
        text_lower = text.lower()

        if "hora" in text_lower:
            current_time = datetime.now().strftime("%H:%M")
            return f"Son las {current_time}, {self.user_name}."

        if "fecha" in text_lower:
            current_date = datetime.now().strftime("%d de %B de %Y")
            return f"Hoy es {current_date}."

        cached_response = self.learning.get_personalized_response(text)
        if cached_response:
            return cached_response

        return None

    def _generate_ai_response(self, text):
        processed_text = self._enhance_input(text)
        response = None

        def generate():
            nonlocal response
            response = self.model.generate(processed_text)

        gen_thread = threading.Thread(target=generate)
        gen_thread.start()
        gen_thread.join(timeout=5)

        if not response:
            return "Disculpa la demora, estoy teniendo dificultades. ¿Podrías repetir o reformular tu solicitud?"
        return self._enhance_response(response)

    def _enhance_input(self, text):
        for wrong, correct in self.learning.preferences['corrections'].items():
            if wrong in text.lower():
                text = text.replace(wrong, correct)

        user_profile = self.learning.get_user_profile()
        context = f"[Usuario: {self.user_name}, Temas favoritos: {', '.join(user_profile['favorite_topics'])}, Patrón de interacción: {user_profile['interaction_pattern']}] "
        return context + text

    def _enhance_response(self, response):
        if not response.startswith(self.user_name):
            response = f"{self.user_name}, {response}"

        if self.learning.preferences.get('informal_style', False):
            response = response.replace("puedo ayudarte", "te puedo ayudar")
            response = response.replace("disculpa", "perdoná")

        if len(response.split()) > 30:
            sentences = response.split('. ')
            response = '. '.join(sentences[:2]) + '.' if len(sentences) > 2 else response

        return response

    def _execute_associated_actions(self, text, response):
        text_lower = text.lower()

        if any(cmd in text_lower for cmd in ["reproduce", "pon", "abre video", "mirar"]):
            query = self._extract_media_query(text_lower)
            if query:
                self.web.play_youtube(query)
                return f"Listo {self.user_name}, estoy reproduciendo {query} en YouTube."

        elif "busca" in text_lower or "buscar" in text_lower:
            query = text_lower.replace("busca", "").replace("buscar", "").strip()
            if query:
                self.web.search_web(query)
                return f"Encontré esto sobre {query}. ¿Te sirve la información?"

        return None

    def _extract_media_query(self, text):
        for pattern in self.learning.preferences.get('media_patterns', []):
            if pattern in text:
                return text.split(pattern)[1].strip()

        for trigger in ["reproduce", "pon", "abre"]:
            if trigger in text:
                return text.split(trigger)[1].strip()

        return None

    def _deactivate_if_inactive(self):
        if time.time() - self.last_interaction > self.response_delay:
            self.is_active = False
            self.voice.speak("Estoy aquí cuando me necesites.")

    def run(self):
        listen_thread = threading.Thread(target=self.listen_loop)
        listen_thread.daemon = True
        listen_thread.start()

        background_thread = threading.Thread(target=self._background_tasks)
        background_thread.daemon = True
        background_thread.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nApagando Jarvis...")
            self.voice.speak(f"Hasta luego, {self.user_name}.")

    def _background_tasks(self):
        while True:
            if not self.is_active and time.time() - self.last_interaction > 60:
                self._warm_up_model()
            self.learning.analyze_interaction_patterns()
            time.sleep(30)

    def _warm_up_model(self):
        try:
            self.model.generate("Mantener modelo activo")
        except:
            pass


if __name__ == "__main__":
    jarvis = Jarvis()
    jarvis.run()
