import speech_recognition as sr
import requests
import asyncio
import json
import os
import webbrowser
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import uuid
from playsound import playsound

# ======================= CONFIGURACIÓN ==========================
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gemma:2b"
VOICE_ID = "es-MX-DaliaNeural"  # Voz cercana a español latino

# ======================== TTS NATURAL ===========================
async def speak(text):
    try:
        from edge_tts import Communicate
        print(f"🤖 {text}")
        nombre_temp = f"temp_{uuid.uuid4().hex}.mp3"
        tts = Communicate(text, voice=VOICE_ID)
        await tts.save(nombre_temp)
        playsound(nombre_temp)
        os.remove(nombre_temp)
    except Exception as e:
        print(f"❌ Error en TTS: {e}")

def speak_threaded(text):
    asyncio.run(speak(text))

# ==================== RECONOCIMIENTO DE VOZ ====================
recognizer = sr.Recognizer()

def listen():
    with sr.Microphone() as source:
        print("🎤 Escuchando...")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        recognizer.pause_threshold = 1.0
        audio = recognizer.listen(source)
    try:
        return recognizer.recognize_google(audio, language="es-AR")
    except sr.UnknownValueError:
        return None

# ======================== LLAMAR AL MODELO ======================
def ask_model(prompt):
    try:
        response = requests.post(OLLAMA_URL, json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False
        }, timeout=15)
        return response.json().get("response", "")
    except Exception:
        return "No pude conectar con el modelo."

# ======================= PERFIL DE USUARIO ======================
def aprender(texto):
    perfil = cargar_perfil()
    if "me gusta" in texto:
        gusto = texto.split("me gusta")[-1].strip()
        if gusto and gusto not in perfil["gustos"]:
            perfil["gustos"].append(gusto)
            guardar_perfil(perfil)

def cargar_perfil():
    if os.path.exists("perfil_usuario.json"):
        with open("perfil_usuario.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return {"gustos": []}

def guardar_perfil(data):
    with open("perfil_usuario.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ========================= FUNCIONES EXTRA =========================
def buscar_en_google(texto):
    query = texto.replace("buscá", "").strip()
    url = f"https://www.google.com/search?q={query}"
    webbrowser.open(url)

def reproducir_youtube(texto):
    busqueda = texto.replace("reproduce", "").replace("en youtube", "").strip()
    query = "+".join(busqueda.split())

    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(f"https://www.youtube.com/results?search_query={query}")
    time.sleep(3)
    try:
        video = driver.find_element("id", "video-title")
        video.click()
    except Exception:
        speak_threaded("No pude reproducirlo.")
        driver.quit()

# ======================= PROCESAR COMANDO =======================
def procesar_comando(texto):
    texto = texto.lower()

    if "me gusta" in texto:
        aprender(texto)
        speak_threaded("Lo voy a recordar.")

    elif "buscá" in texto:
        speak_threaded("Buscando en Google...")
        buscar_en_google(texto)

    elif "reproduce" in texto and "youtube" in texto:
        speak_threaded("Buscando en YouTube...")
        reproducir_youtube(texto)

    else:
        respuesta = ask_model(texto)
        speak_threaded(respuesta)

# =========================== MAIN LOOP ===========================
def main():
    speak_threaded("Hola, ¿en qué te puedo ayudar?")
    while True:
        texto = listen()
        if texto:
            print(f"🙋 Dijiste: {texto}")
            procesar_comando(texto)
        else:
            speak_threaded("No entendí, ¿podés repetirlo?")

if __name__ == "__main__":
    main()
