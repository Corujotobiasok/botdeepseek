import os
import time
import threading
import speech_recognition as sr
from gtts import gTTS
import pygame
from ollama import Client

# Configuración inicial
client = Client(host='http://localhost:11434')
model_name = 'gemma:2b'

# Configurar pygame para reproducción de audio
pygame.mixer.init()

# Configuración del reconocimiento de voz
recognizer = sr.Recognizer()
recognizer.pause_threshold = 2.0  # Tiempo más largo para pausas
recognizer.phrase_threshold = 0.8  # Menos sensible al inicio del habla
recognizer.non_speaking_duration = 0.8  # Tiempo más corto para considerar el fin del habla

def hablar(texto, velocidad=False):
    """Función para convertir texto a voz con acento argentino"""
    try:
        # Ajustar el texto para que suene más natural en argentino
        texto_ajustado = texto.replace("tú", "vos").replace("ti", "vos").replace("tuyo", "tuyo")
        
        # Crear el archivo de audio
        tts = gTTS(text=texto_ajustado, lang='es', tld='com.ar')  # Usamos el dominio argentino
        
        # Guardar el archivo temporal
        temp_file = "temp_voice.mp3"
        tts.save(temp_file)
        
        # Reproducir el audio
        pygame.mixer.music.load(temp_file)
        pygame.mixer.music.play()
        
        # Esperar a que termine la reproducción
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
            
        # Eliminar el archivo temporal
        os.remove(temp_file)
        
    except Exception as e:
        print(f"Error en la función hablar: {e}")

def escuchar():
    """Función para escuchar y convertir voz a texto"""
    with sr.Microphone() as source:
        print("Escuchando... (di algo)")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        
        try:
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=15)
            print("Procesando...")
            
            # Usar reconocimiento de Google con ajuste para español argentino
            texto = recognizer.recognize_google(audio, language="es-AR")
            print(f"Tú dijiste: {texto}")
            return texto.lower()
            
        except sr.WaitTimeoutError:
            print("Tiempo de espera agotado, no se detectó voz.")
            return ""
        except sr.UnknownValueError:
            print("No pude entender lo que dijiste.")
            return ""
        except Exception as e:
            print(f"Error en el reconocimiento de voz: {e}")
            return ""

def generar_respuesta(prompt):
    """Función para generar una respuesta usando Ollama con Gemma:2b"""
    try:
        response = client.generate(
            model=model_name,
            prompt=f"Responde en español argentino, de manera coloquial pero educada. {promrompt}",
            stream=False,
            options={
                'temperature': 0.7,
                'num_ctx': 2048
            }
        )
        
        # Limpiar la respuesta
        respuesta = response['response'].strip()
        
        # Reemplazar algunos términos para que suene más argentino
        replacements = {
            "puedo ayudarte": "te puedo dar una mano",
            "puedes preguntarme": "podés preguntarme",
            "tú": "vos",
            "para ti": "para vos",
            "cierto": "posta",
            "claro": "dale",
            "por favor": "porfa",
            "bueno": "buenísimo"
        }
        
        for original, reemplazo in replacements.items():
            respuesta = respuesta.replace(original, reemplazo)
            
        return respuesta
        
    except Exception as e:
        print(f"Error al generar la respuesta: {e}")
        return "Che, no pude procesar tu pregunta. ¿Podés repetirla?"

def conversacion():
    """Función principal para manejar la conversación"""
    hablar("¡Hola che! ¿Cómo andás? Decime en qué te puedo dar una mano.", velocidad=True)
    
    while True:
        texto = escuchar()
        
        if not texto:
            hablar("No te escuché bien, ¿podés repetirlo?", velocidad=True)
            continue
            
        if "adiós" in texto or "chau" in texto or "hasta luego" in texto:
            hablar("¡Bueno, nos vemos! Cualquier cosa me chiflás.", velocidad=True)
            break
            
        respuesta = generar_respuesta(texto)
        print(f"Gemma: {respuesta}")
        hablar(respuesta, velocidad=True)

if __name__ == "__main__":
    print("Iniciando asistente con Gemma:2b...")
    conversacion()