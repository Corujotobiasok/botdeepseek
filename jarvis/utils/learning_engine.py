import json
import os
import pickle
import numpy as np
from collections import defaultdict
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
import hashlib

class LearningEngine:
    def __init__(self, user_id="default"):
        self.user_id = hashlib.md5(user_id.encode()).hexdigest()
        self.data_dir = "user_data"
        self.data_file = f"{self.data_dir}/{self.user_id}_preferences.pkl"
        self.interaction_log = f"{self.data_dir}/{self.user_id}_interactions.log"
        
        # Datos del usuario
        self.preferences = {
            'frequent_commands': defaultdict(int),
            'preferred_responses': {},
            'corrections': {},
            'dislikes': set(),
            'preferred_topics': defaultdict(int),
            'interaction_times': [],
            'command_patterns': defaultdict(list),
            'media_patterns': []
        }
        
        # Modelos de similitud
        self.vectorizer = TfidfVectorizer(max_features=500)
        self.knn = NearestNeighbors(n_neighbors=1, algorithm='ball_tree')
        self.commands_db = []
        
        self.load_data()

    # ... (métodos load_data, save_data, log_interaction del anterior)

    def analyze_interaction_patterns(self):
        """Analiza patrones para mejorar respuestas"""
        # Actualiza patrones de comandos de medios
        if os.path.exists(self.interaction_log):
            with open(self.interaction_log, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        if any(cmd in entry['command'].lower() for cmd in ["reproduce", "pon"]):
                            self._extract_media_pattern(entry['command'])
                    except:
                        continue
            self.save_data()

    def _extract_media_pattern(self, command):
        """Extrae patrones de comandos de medios"""
        words = command.lower().split()
        triggers = ["reproduce", "pon", "abre", "quiero"]
        
        for i, word in enumerate(words):
            if word in triggers and i < len(words)-1:
                pattern = " ".join(words[i:i+2])
                if pattern not in self.preferences['media_patterns']:
                    self.preferences['media_patterns'].append(pattern)
                    return True
        return False

    def get_contextual_response(self, command, context):
        """Genera respuesta considerando contexto"""
        # 1. Buscar respuesta exacta
        if command in self.preferences['preferred_responses']:
            return self.preferences['preferred_responses'][command]
        
        # 2. Buscar por similitud semántica
        similar = self._find_similar_command(command)
        if similar:
            response = self.preferences['preferred_responses'].get(similar)
            if response:
                return self._adapt_response(response, context)
        
        # 3. Generar basado en patrones
        return None

    def _adapt_response(self, response, context):
        """Adapta una respuesta al contexto actual"""
        # Reemplazar marcadores de tiempo
        if "[hora]" in response:
            current_time = datetime.now().strftime("%H:%M")
            response = response.replace("[hora]", current_time)
        
        # Agregar nombre si no está
        if "[nombre]" in response:
            response = response.replace("[nombre]", context.get('user_name', ''))
        elif not any(response.startswith(x) for x in ["Señor", context.get('user_name', '')]):
            response = f"{context.get('user_name', 'Señor')}, {response}"
        
        return response

    # ... (otros métodos del anterior)