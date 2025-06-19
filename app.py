import ollama
import queue
import sounddevice as sd
import numpy as np
import pyttsx3
import json
import os
import sys
import time
from vosk import Model, KaldiRecognizer

# Ruta al modelo de voz (cambia esto según tu sistema)
VOSK_MODEL_PATH = "modelos/vosk-es"

# Inicializamos Text to Speech con acento argentino
engine = pyttsx3.init()
engine.setProperty('rate', 160)  # velocidad
engine.setProperty('volume', 1.0)

# Seleccionamos una voz con acento español (argento si está disponible)
for voice in engine.getProperty('voices'):
    if "spanish" in voice.name.lower() or "español" in voice.name.lower():
        engine.setProperty('voice', voice.id)
        break

# Inicializamos Vosk
if not os.path.exists(VOSK_MODEL_PATH):
    print("¡Error! No se encontró el modelo de Vosk. Descargalo desde https://alphacephei.com/vosk/models")
    sys.exit(1)

model = Model(VOSK_MODEL_PATH)
rec = KaldiRecognizer(model, 16000)
q = queue.Queue()

def callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

def escuchar_microfono(timeout=15):
    print("🎤 Esperando tu pregunta (tomate tu tiempo)...")
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                           channels=1, callback=callback):
        data = bytes()
        start_time = time.time()

        while True:
            if time.time() - start_time > timeout:
                print("⏱️ Tiempo de escucha agotado.")
                break
            try:
                data += q.get(timeout=timeout)
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    texto = result.get("text", "")
                    if texto:
                        print(f"🗣️ Dijiste: {texto}")
                        return texto
            except queue.Empty:
                pass
    return ""

def responder_voz(texto):
    print(f"🤖 Jarvis dice: {texto}")
    engine.say(texto)
    engine.runAndWait()

def responder_con_gemma(prompt):
    print("🧠 Pensando con Gemma...")
    respuesta = ollama.chat(
        model="gemma:2b",
        messages=[
            {"role": "system", "content": "Actuá como un asistente argentino muy piola, con respuestas naturales y empáticas."},
            {"role": "user", "content": prompt}
        ]
    )
    return respuesta['message']['content']

def main():
    print("🧠 JARVIS ARG comenzando...\nDecí algo cuando estés listo (tarda más en escucharte).")

    while True:
        texto_usuario = escuchar_microfono(timeout=20)
        if not texto_usuario:
            responder_voz("No te entendí, ¿podés repetir más claro?")
            continue

        if "salir" in texto_usuario.lower():
            responder_voz("Listo, nos vemos, maestro.")
            break

        respuesta = responder_con_gemma(texto_usuario)
        responder_voz(respuesta)

if __name__ == "__main__":
    main()
