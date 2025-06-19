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
