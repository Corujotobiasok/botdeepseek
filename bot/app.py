import os
import time
import pygame
import speech_recognition as sr
from gtts import gTTS
import webbrowser
from transformers import AutoModelForCausalLM, AutoTokenizer

# Configuración inicial
pygame.init()
screen = pygame.display.set_mode((800, 400))
pygame.display.set_caption("DeepSeek R1 Assistant")

# Cargar imágenes de los ojos (ajusta las rutas según tu estructura)
def load_eye_assets():
    return {
        "normal": pygame.image.load("static/ojos_normal.png").convert_alpha(),
        "buscar": pygame.image.load("static/ojos_buscar.png").convert_alpha(),
        "hablar": pygame.image.load("static/ojos_hablar.png").convert_alpha(),
    }

eyes = load_eye_assets()
current_eye_state = "normal"

# Cargar modelo DeepSeek R1 (asegúrate de tener el modelo en /models)
tokenizer = AutoTokenizer.from_pretrained("models/deepseek-r1")
model = AutoModelForCausalLM.from_pretrained("models/deepseek-r1")

# Reconocimiento de voz
def listen():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("🦾 Escuchando... Di 'DeepSeek' para activar.")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source, timeout=5)
        
        try:
            text = recognizer.recognize_google(audio, language="es-ES").lower()
            print(f"Usuario: {text}")
            return text
        except sr.UnknownValueError:
            print("No te entendí.")
            return ""
        except sr.RequestError:
            print("Error en el servicio de voz.")
            return ""

# Síntesis de voz
def speak(text):
    global current_eye_state
    current_eye_state = "hablar"
    tts = gTTS(text=text, lang="es", slow=False)
    tts.save("response.mp3")
    os.system("start response.mp3" if os.name == 'nt' else "afplay response.mp3")
    time.sleep(len(text) * 0.05)  # Ajusta según la duración del audio
    current_eye_state = "normal"

# Búsqueda web + resumen con R1
def search_and_summarize(query):
    global current_eye_state
    current_eye_state = "buscar"
    
    # Abrir búsqueda en Google
    webbrowser.open(f"https://www.google.com/search?q={query}")
    
    # Generar resumen con DeepSeek R1
    input_ids = tokenizer.encode(f"Resume brevemente: {query}", return_tensors="pt")
    output = model.generate(input_ids, max_length=150)
    summary = tokenizer.decode(output[0], skip_special_tokens=True)
    
    speak(f"Según mi búsqueda: {summary}")
    current_eye_state = "normal"

# Bucle principal
def main():
    global current_eye_state
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        # Dibujar ojos según el estado actual
        screen.fill((0, 0, 0))
        screen.blit(eyes[current_eye_state], (300, 100))
        pygame.display.flip()
        
        # Escuchar comandos
        command = listen()
        
        if "deepseek" in command:
            speak("¿En qué puedo ayudarte?")
            time.sleep(1)
            new_command = listen()
            
            if "busca" in new_command:
                query = new_command.replace("busca", "").strip()
                if query:
                    search_and_summarize(query)
            elif "adiós" in new_command:
                speak("Hasta luego. Desconectando.")
                running = False
            else:
                speak("No entendí el comando.")
    
    pygame.quit()

if __name__ == "__main__":
    main()