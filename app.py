import speech_recognition as sr
import requests
import edge_tts
import asyncio
import json
import os
import webbrowser
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import threading
import time

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gemma:2b"

recognizer = sr.Recognizer()

# Configurar voz de edge-tts (más natural y latinoamericana)
async def speak(text):
    print(f"🤖 {text}")
    communicate = edge_tts.Communicate(text, voice="es-MX-DaliaNeural")
    await communicate.play()

def speak_thread(text):
    asyncio.run(speak(text))

def listen():
    with sr.Microphone() as source:
        print("🎤 Esperando tu voz...")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        recognizer.pause_threshold = 1.0
        audio = recognizer.listen(source)

    try:
        return recognizer.recognize_google(audio, language="es-AR")
    except sr.UnknownValueError:
        return None

def ask_model(prompt):
    try:
        response = requests.post(OLLAMA_URL, json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False
        }, timeout=10)
        return response.json().get("response", "")
    except Exception:
        return "Hubo un error al conectar con el modelo."

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
        first_video = driver.find_element("id", "video-title")
        first_video.click()
    except:
        speak_thread("No pude reproducirlo.")
        driver.quit()

def procesar_comando(texto):
    texto = texto.lower()
    if "me gusta" in texto:
        aprender(texto)
        speak_thread("Lo voy a recordar")
    elif "buscá" in texto:
        speak_thread("Buscando en Google...")
        buscar_en_google(texto)
    elif "reproduce" in texto and "youtube" in texto:
        speak_thread("Buscando en YouTube...")
        reproducir_youtube(texto)
    else:
        respuesta = ask_model(texto)
        speak_thread(respuesta)

def main():
    speak_thread("Hola, ¿en qué te ayudo?")
    while True:
        texto = listen()
        if texto:
            print(f"🙋 Dijiste: {texto}")
            procesar_comando(texto)
        else:
            speak_thread("No entendí, ¿podés repetirlo?")

if __name__ == "__main__":
    main()
