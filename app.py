import streamlit as st
import json
import paho.mqtt.client as mqtt
import time
from gtts import gTTS
from deep_translator import GoogleTranslator
import os
from io import BytesIO
import base64
import openai  # ✅ Cambiado

# Configura tu API Key de OpenAI
openai.api_key = st.secrets["openai_api_key"]  # ✅ Nueva forma

MQTT_BROKER = "broker.mqttdashboard.com"
MQTT_PORT = 1883
MQTT_TOPIC = "selector/animal"

# Variables de estado
if 'sensor_data' not in st.session_state:
    st.session_state.sensor_data = None
if 'story' not in st.session_state:
    st.session_state.story = ""
if 'audio' not in st.session_state:
    st.session_state.audio = None
if 'idioma' not in st.session_state:
    st.session_state.idioma = "es"

# MQTT
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

# 🧠 IA: Generar historia
def generar_historia(animal, lugar):
    prompt = f"Cuéntame una historia para niños donde un {animal} vive una aventura en {lugar}. Usa un lenguaje sencillo y divertido."
    response = openai.chat.completions.create(  # ✅ Cambiado
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Eres un narrador de historias infantiles."},
            {"role": "user", "content": prompt}
        ]
    )
    historia = response.choices[0].message.content.strip()
    return historia

# 🔊 Texto a voz
def generar_audio(texto, idioma):
    tts = gTTS(text=texto, lang=idioma)
    audio_buffer = BytesIO()
    tts.write_to_fp(audio_buffer)
    audio_buffer.seek(0)
    return audio_buffer

# 🌍 Traducción
def traducir(texto, destino):
    return GoogleTranslator(source='auto', target=destino).translate(texto)

# 🌐 Interfaz
st.set_page_config(page_title="Animal y Lugar", page_icon="🦁")
st.title("🌍 ¡Aventura Animal!")

st.selectbox("Selecciona el idioma", ["Español", "Inglés"], index=0, key="idioma")

if st.button("Obtener Lectura del ESP32"):
    with st.spinner("Esperando datos..."):
        data = get_mqtt_message()
        st.session_state.sensor_data = data

if st.session_state.sensor_data:
    animal = st.session_state.sensor_data.get("animal", "N/A")
    lugar = st.session_state.sensor_data.get("lugar", "N/A")

    st.success("Datos recibidos correctamente")
    st.metric("Animal", animal)
    st.metric("Lugar", lugar)

    if st.button("Contar historia 🧚"):
        historia = generar_historia(animal, lugar)

        # Traducción si se desea en inglés
        idioma = "es" if st.session_state.idioma == "Español" else "en"
        if idioma == "en":
            historia = traducir(historia, "en")

        st.session_state.story = historia
        st.session_state.audio = generar_audio(historia, idioma)
    
    if st.session_state.story:
        st.subheader("📖 Historia")
        st.write(st.session_state.story)

        st.subheader("🎧 Escucha la historia")
        st.audio(st.session_state.audio, format='audio/mp3')
else:
    st.info("Presiona el botón para obtener los datos actuales desde el ESP32.")

