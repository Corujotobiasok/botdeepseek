import time
import threading
import json
from datetime import datetime
from utils.voice_engine import VoiceEngine
from utils.web_controller import WebController
from utils.learning_engine import LearningEngine
from utils.response_manager import ResponseManager
import google.gemma as gemma  # Asegúrate de tener la importación correcta

class Jarvis:
    def __init__(self):
        # Cargar configuración
        with open('config.json') as config_file:
            self.config = json.load(config_file)

        # Configuración inicial
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
        """Carga el modelo Gemma:2b con configuración optimizada"""
        try:
            config = {
                'max_length': 150,  # Respuestas más cortas = más rápidas
                'temperature': 0.7,  # Balance entre creatividad y precisión
                'top_k': 40,
                'top_p': 0.9
            }
            model = gemma.load_model('gemma-2b', **config)
            print("Modelo Gemma-2b cargado con configuración optimizada.")
            return model
        except Exception as e:
            print(f"Error al cargar el modelo: {e}")
            return None

    def listen_loop(self):
        """Bucle principal de escucha optimizado"""
        while True:
            if not self.is_active and time.time() - self.last_interaction > 300:
                time.sleep(0.5)  # Reduce CPU cuando está inactivo
                continue

            print("\nEscuchando... (Modo activo)" if self.is_active else "\nEscuchando... (Modo espera)")
            text = self.voice.listen(timeout=3 if self.is_active else 1)
            
            # Verificar activación
            if text and self.activation_word in text.lower():
                self._activate_assistant()
                continue
                
            # Procesar comando si está activo
            if self.is_active and text:
                self._process_user_command(text)

    def _activate_assistant(self):
        """Activa el asistente con respuesta inmediata"""
        self.is_active = True
        self.last_activation = time.time()
        self.voice.speak(f"¿En qué puedo ayudarte, {self.user_name}?")
        self.last_interaction = time.time()

    def _process_user_command(self, text):
        """Procesa el comando del usuario con feedback continuo"""
        self.last_interaction = time.time()
        
        # Paso 1: Reconocimiento inmediato
        self.voice.speak(self.response_manager.get_acknowledgement())
        
        # Paso 2: Procesamiento en paralelo con feedback
        processing_thread = threading.Thread(
            target=self._handle_command_processing,
            args=(text,)
        )
        processing_thread.start()
        
        # Feedback mientras procesa
        self._provide_processing_feedback(text)
        
        processing_thread.join()

    def _handle_command_processing(self, text):
        """Maneja el procesamiento del comando"""
        self.is_processing = True
        
        try:
            # Paso 1: Verificar acciones rápidas
            quick_action_response = self._check_quick_actions(text)
            if quick_action_response:
                self.voice.speak(quick_action_response)
                return
            
            # Paso 2: Procesamiento con IA
            start_time = time.time()
            
            # Respuesta inmediata si es posible
            cached_response = self.learning.get_personalized_response(text)
            if cached_response:
                self.voice.speak(cached_response)
                return
            
            # Respuesta generativa con feedback
            if time.time() - start_time > 1.5:  # Si está tardando
                self.voice.speak("Estoy analizando tu solicitud...")
            
            full_response = self._generate_ai_response(text)
            
            # Paso 3: Ejecutar acciones asociadas
            action_result = self._execute_associated_actions(text, full_response)
            
            # Paso 4: Responder
            final_response = action_result if action_result else full_response
            self.voice.speak(final_response)
            
            # Paso 5: Aprender de la interacción
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
        """Proporciona feedback durante el procesamiento"""
        # Feedback inicial inmediato
        time.sleep(0.3)  # Pequeña pausa natural
        
        # Feedback intermedio si está tardando
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
        """Verifica acciones que pueden responderse sin IA"""
        text_lower = text.lower()
        
        # Comandos de sistema
        if "hora" in text_lower:
            current_time = datetime.now().strftime("%H:%M")
            return f"Son las {current_time}, {self.user_name}."
            
        if "fecha" in text_lower:
            current_date = datetime.now().strftime("%d de %B de %Y")
            return f"Hoy es {current_date}."
            
        # Comandos aprendidos
        cached_response = self.learning.get_personalized_response(text)
        if cached_response:
            return cached_response
            
        return None

    def _generate_ai_response(self, text):
        """Genera respuesta optimizada con el modelo de IA"""
        # Preprocesamiento mejorado
        processed_text = self._enhance_input(text)
        
        # Generación de respuesta con timeout
        response = None
        def generate():
            nonlocal response
            response = self.model.generate(processed_text)
        
        gen_thread = threading.Thread(target=generate)
        gen_thread.start()
        gen_thread.join(timeout=5)  # Timeout para evitar demoras
        
        if not response:
            return "Disculpa la demora, estoy teniendo dificultades. ¿Podrías repetir o reformular tu solicitud?"
        
        # Post-procesamiento
        return self._enhance_response(response)

    def _enhance_input(self, text):
        """Mejora el input para mejor comprensión"""
        # 1. Aplicar correcciones aprendidas
        for wrong, correct in self.learning.preferences['corrections'].items():
            if wrong in text.lower():
                text = text.replace(wrong, correct)
        
        # 2. Agregar contexto de usuario
        user_profile = self.learning.get_user_profile()
        context = f"[Usuario: {self.user_name}, Temas favoritos: {', '.join(user_profile['favorite_topics'])}, Patrón de interacción: {user_profile['interaction_pattern']}] "
        
        return context + text

    def _enhance_response(self, response):
        """Mejora la respuesta para sonar más natural"""
        # 1. Personalizar con nombre
        if not response.startswith(self.user_name):
            response = f"{self.user_name}, {response}"
        
        # 2. Aplicar estilo aprendido
        if self.learning.preferences.get('informal_style', False):
            response = response.replace("puedo ayudarte", "te puedo ayudar")
            response = response.replace("disculpa", "perdoná")
        
        # 3. Acortar respuestas largas
        if len(response.split()) > 30:
            sentences = response.split('. ')
            response = '. '.join(sentences[:2]) + '.' if len(sentences) > 2 else response
        
        return response

    def _execute_associated_actions(self, text, response):
        """Ejecuta acciones asociadas al comando"""
        text_lower = text.lower()
        
        # Control de YouTube
        if any(cmd in text_lower for cmd in ["reproduce", "pon", "abre video", "mirar"]):
            query = self._extract_media_query(text_lower)
            if query:
                self.web.play_youtube(query)
                return f"Listo {self.user_name}, estoy reproduciendo {query} en YouTube."
        
        # Búsqueda web
        elif "busca" in text_lower or "buscar" in text_lower:
            query = text_lower.replace("busca", "").replace("buscar", "").strip()
            if query:
                self.web.search_web(query)
                return f"Encontré esto sobre {query}. ¿Te sirve la información?"
        
        return None

    def _extract_media_query(self, text):
        """Extrae la consulta de medios mejorado"""
        # Usar aprendizaje para entender formatos preferidos
        for pattern in self.learning.preferences.get('media_patterns', []):
            if pattern in text:
                return text.split(pattern)[1].strip()
        
        # Enfoque por defecto
        for trigger in ["reproduce", "pon", "abre"]:
            if trigger in text:
                return text.split(trigger)[1].strip()
        
        return None

    def _deactivate_if_inactive(self):
        """Desactiva el asistente si lleva tiempo inactivo"""
        if time.time() - self.last_interaction > self.response_delay:
            self.is_active = False
            self.voice.speak("Estoy aquí cuando me necesites.")

    def run(self):
        """Inicia el asistente optimizado"""
        # Hilo para escucha continua
        listen_thread = threading.Thread(target=self.listen_loop)
        listen_thread.daemon = True
        listen_thread.start()
        
        # Hilo para tareas en segundo plano
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
        """Tareas en segundo plano para mejorar rendimiento"""
        while True:
            # Precargar modelos cuando está inactivo
            if not self.is_active and time.time() - self.last_interaction > 60:
                self._warm_up_model()
            
            # Aprendizaje continuo
            self.learning.analyze_interaction_patterns()
            time.sleep(30)

    def _warm_up_model(self):
        """Mantiene el modelo caliente para respuestas rápidas"""
        try:
            self.model.generate("Mantener modelo activo", max_length=1)
        except:
            pass

if __name__ == "__main__":
    jarvis = Jarvis()
    jarvis.run()