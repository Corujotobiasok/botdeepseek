import random
from datetime import datetime

class ResponseManager:
    def __init__(self):
        self.acknowledgements = [
            "Voy a ver...",
            "Déjame comprobar...",
            "Un momento...",
            "Estoy en eso...",
            "Ya mismo...",
            "A ver...",
            "Déjame pensar..."
        ]
        
        self.processing_phrases = {
            'search': [
                "Estoy buscando información...",
                "Consultando mis fuentes...",
                "Buscando los datos más recientes..."
            ],
            'media': [
                "Preparando la reproducción...",
                "Configurando el reproductor...",
                "Iniciando el video..."
            ],
            'generic': [
                "Procesando tu solicitud...",
                "Analizando lo que necesitas...",
                "Dándole vueltas a tu petición..."
            ]
        }

    def get_acknowledgement(self):
        """Obtiene una confirmación de escucha"""
        return random.choice(self.acknowledgements)

    def get_processing_phrase(self, command_type='generic'):
        """Obtiene una frase de procesamiento según el tipo"""
        return random.choice(self.processing_phrases.get(command_type, self.processing_phrases['generic']))

    def get_time_based_greeting(self):
        """Saludo según la hora del día"""
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return "Buenos días"
        elif 12 <= hour < 19:
            return "Buenas tardes"
        else:
            return "Buenas noches"