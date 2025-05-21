import streamlit as st
import json
import paho.mqtt.client as mqtt
import time
from gtts import gTTS
from io import BytesIO
import base64
from deep_translator import GoogleTranslator
import requests
import openai

# --- Configuración MQTT
MQTT_BROKER = "broker.mqttdashboard.com"
MQTT_PORT = 1883
MQTT_TOPIC = "selector/animal"

# --- Inicialización de sesión
if 'sensor_data' not in st.session_state:
    st.session_state.sensor_data = None
if 'language' not in st.session_state:
    st.session_state.language = 'es'
if 'openai_key' not in st.session_state:
    st.session_state.openai_key = ''

# --- Función para recibir mensaje del ESP32
def get_mqtt_message():
    message_received = {"received": False, "payload": None}
    def on_message(client, userdata, message):
        try:
            payload = json.loads(message.payload.decode())
            message_received["payload"] = payload
            message_received["received"] = True
        except Exception as e:
            st.error(f"Error al procesar mensaje: {e}")
    try:
        client = mqtt.Client()
        client.on_message = on_message
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.subscribe(MQTT_TOPIC)
        client.loop_start()
        timeout = time.time() + 5
        while not message_received["received"] and time.time() < timeout:
            time.sleep(0.1)
        client.loop_stop()
        client.disconnect()
        return message_received["payload"]
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

# --- Función para generar historia con GPT
def generar_historia(animal, lugar, api_key):
    openai.api_key = api_key
    prompt = (
        f"Escribe una historia creativa y divertida para niños de al menos un párrafo, "
        f"que tenga como protagonista a un {animal} que vive en {lugar}. "
        f"La historia debe ser mágica, entretenida y educativa. No debe ser una lista, sino una narración completa."
    )
    try:
        respuesta = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Eres un narrador de cuentos mágicos para niños."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=400
        )
        historia = respuesta.choices[0].message.content.strip()

        if st.session_state.language != 'es':
            historia = GoogleTranslator(source='auto', target=st.session_state.language).translate(historia)

        return historia

    except Exception as e:
        st.error(f"No se pudo generar la historia: {e}")
        return f"Había una vez un {animal} que vivía en {lugar}..."

# --- Función para texto a voz
def reproducir_audio(texto):
    try:
        tts = gTTS(text=texto, lang=st.session_state.language)
        audio_fp = BytesIO()
        tts.write_to_fp(audio_fp)
        audio_fp.seek(0)
        audio_base64 = base64.b64encode(audio_fp.read()).decode()
        st.audio(f"data:audio/mp3;base64,{audio_base64}", format="audio/mp3")
    except Exception as e:
        st.error("No se pudo generar el audio")

# --- Función para imagen desde Unsplash
def obtener_imagen(animal, lugar):
    query = f"{animal} en {lugar}"
    url = f"https://source.unsplash.com/600x400/?{query}"
    st.image(url, caption=f"{animal.title()} en {lugar.title()}")

# --- Interfaz
st.set_page_config(page_title="Animal y Lugar", page_icon="🌍")
st.title("🌟 Aventura Interactiva: Animal y Lugar")

# --- Input de API Key
st.text_input("🔑 Ingresa tu clave de OpenAI", type="password", key="openai_key")
st.selectbox("🌐 Selecciona idioma", options=["es", "en", "fr", "pt"], key="language",
             format_func=lambda x: {"es": "Español", "en": "Inglés", "fr": "Francés", "pt": "Portugués"}[x])

# --- Botón para obtener datos
if st.button("📡 Obtener Lectura del ESP32"):
    if not st.session_state.openai_key:
        st.warning("Por favor ingresa tu clave de OpenAI antes de continuar.")
    else:
        with st.spinner("Esperando datos..."):
            data = get_mqtt_message()
            st.session_state.sensor_data = data

# --- Visualización de historia
if st.session_state.sensor_data and st.session_state.openai_key:
    st.success("✅ Datos recibidos correctamente")
    animal = st.session_state.sensor_data.get("animal", "N/A")
    lugar = st.session_state.sensor_data.get("lugar", "N/A")
    st.metric("🐾 Animal", animal)
    st.metric("🌍 Lugar", lugar)

    st.subheader("📖 Historia mágica")
    historia = generar_historia(animal, lugar, st.session_state.openai_key)
    st.write(historia)

    st.subheader("🎧 Escuchar historia")
    reproducir_audio(historia)

    st.subheader("🖼️ Imagen sugerida")
    obtener_imagen(animal, lugar)
elif not st.session_state.openai_key:
    st.info("🔑 Ingresa tu clave de OpenAI para generar una historia mágica.")
else:
    st.info("Presiona el botón para obtener los datos actuales desde el ESP32.")
