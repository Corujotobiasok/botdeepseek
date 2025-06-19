import speech_recognition as sr
import pyttsx3
import requests
import time

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gemma:2b"

engine = pyttsx3.init()
recognizer = sr.Recognizer()

def speak(text):
    engine.say(text)
    engine.runAndWait()

def listen():
    with sr.Microphone() as source:
        print("🎤 Esperando tu pregunta...")
        recognizer.pause_threshold = 1.5  # tolera pausas
        audio = recognizer.listen(source)
    try:
        return recognizer.recognize_google(audio, language="es-AR")
    except sr.UnknownValueError:
        return None

def ask_model(prompt):
    response = requests.post(OLLAMA_URL, json={
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    })
    data = response.json()
    return data.get("response", "No entendí la respuesta")

def main():
    speak("Hola, soy tu asistente. ¿En qué te puedo ayudar?")
    while True:
        query = listen()
        if query:
            print(f"🙋 Dijiste: {query}")
            answer = ask_model(query)
            print(f"🤖 Respuesta: {answer}")
            speak(answer)
        else:
            speak("No entendí, ¿podés repetirlo?")

if __name__ == "__main__":
    main()
import speech_recognition as sr
import pyttsx3
import requests
import time
import json
import webbrowser
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gemma:2b"

# Iniciar TTS
engine = pyttsx3.init()
engine.setProperty('rate', 160)  # velocidad
voices = engine.getProperty('voices')
# Elegí voz masculina en español (depende del sistema)
for voice in voices:
    if "spanish" in voice.name.lower() or "español" in voice.name.lower():
        engine.setProperty('voice', voice.id)
        break

def speak(text):
    print(f"🤖 {text}")
    engine.say(text)
    engine.runAndWait()

# Escuchar al usuario
recognizer = sr.Recognizer()
def listen():
    with sr.Microphone() as source:
        print("🎤 Esperando tu voz...")
        recognizer.pause_threshold = 1.5
        audio = recognizer.listen(source)
    try:
        return recognizer.recognize_google(audio, language="es-AR")
    except sr.UnknownValueError:
        return None

# Llamar a modelo local
def ask_model(prompt):
    response = requests.post(OLLAMA_URL, json={
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    })
    return response.json().get("response", "")

# Aprender de vos
def aprender(texto):
    perfil = cargar_perfil()
    if "me gusta" in texto:
        gusto = texto.split("me gusta")[-1].strip()
        if gusto not in perfil["gustos"]:
            perfil["gustos"].append(gusto)
            guardar_perfil(perfil)

def cargar_perfil():
    if os.path.exists("perfil_usuario.json"):
        with open("perfil_usuario.json", "r") as f:
            return json.load(f)
    return {"gustos": []}

def guardar_perfil(data):
    with open("perfil_usuario.json", "w") as f:
        json.dump(data, f)

# Buscar en internet
def buscar_en_google(texto):
    query = texto.replace("buscá", "").strip()
    url = f"https://www.google.com/search?q={query}"
    webbrowser.open(url)

# Reproducir en YouTube con Selenium
def reproducir_youtube(texto):
    busqueda = texto.replace("reproduce", "").replace("en youtube", "").strip()
    query = "+".join(busqueda.split())

    # Configuración de Chrome sin GUI
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    #chrome_options.add_argument("--headless")  # si querés sin abrir ventana
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(f"https://www.youtube.com/results?search_query={query}")

    time.sleep(3)
    try:
        first_video = driver.find_element("id", "video-title")
        first_video.click()
    except Exception as e:
        speak("No pude reproducirlo.")
        driver.quit()

# Procesamiento de comando
def procesar_comando(texto):
    texto = texto.lower()

    if "me gusta" in texto:
        aprender(texto)
        speak("Lo voy a recordar")

    elif "buscá" in texto:
        speak("Buscando en Google...")
        buscar_en_google(texto)

    elif "reproduce" in texto and "youtube" in texto:
        speak("Buscando en YouTube...")
        reproducir_youtube(texto)

    else:
        respuesta = ask_model(texto)
        speak(respuesta)

# Main loop
def main():
    speak("Hola, ¿en qué te ayudo?")
    while True:
        texto = listen()
        if texto:
            print(f"🙋 Dijiste: {texto}")
            procesar_comando(texto)
        else:
            speak("No entendí bien, ¿podés repetir?")

if __name__ == "__main__":
    main()
