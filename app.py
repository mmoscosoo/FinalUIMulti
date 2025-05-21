import streamlit as st
import json
import paho.mqtt.client as mqtt
import time
from gtts import gTTS
from io import BytesIO
import base64
from deep_translator import GoogleTranslator
import requests

MQTT_BROKER = "broker.mqttdashboard.com"
MQTT_PORT = 1883
MQTT_TOPIC = "selector/animal"

if 'sensor_data' not in st.session_state:
    st.session_state.sensor_data = None
if 'language' not in st.session_state:
    st.session_state.language = 'es'

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

def generar_historia(animal, lugar):
    historia = f"Había una vez un {animal} que vivía en {lugar}. Un día, decidió explorar nuevos horizontes y vivió una gran aventura."
    if st.session_state.language != 'es':
        historia = GoogleTranslator(source='auto', target=st.session_state.language).translate(historia)
    return historia

def reproducir_audio(texto):
    tts = gTTS(text=texto, lang=st.session_state.language)
    audio_fp = BytesIO()
    tts.write_to_fp(audio_fp)
    audio_fp.seek(0)
    audio_base64 = base64.b64encode(audio_fp.read()).decode()
    st.audio(f"data:audio/mp3;base64,{audio_base64}", format="audio/mp3")

def obtener_imagen(animal, lugar):
    query = f"{animal} en {lugar}"
    url = f"https://source.unsplash.com/600x400/?{query}"
    st.image(url, caption=f"{animal.title()} en {lugar.title()}")

st.set_page_config(page_title="Animal y Lugar", page_icon="🌍")
st.title("🌟 Aventura Interactiva: Animal y Lugar")

st.selectbox("Selecciona idioma", options=["es", "en", "fr", "pt"], key="language", format_func=lambda x: {"es": "Español", "en": "Inglés", "fr": "Francés", "pt": "Portugués"}[x])

if st.button("Obtener Lectura del ESP32"):
    with st.spinner("Esperando datos..."):
        data = get_mqtt_message()
        st.session_state.sensor_data = data

if st.session_state.sensor_data:
    st.success("Datos recibidos correctamente")
    animal = st.session_state.sensor_data.get("animal", "N/A")
    lugar = st.session_state.sensor_data.get("lugar", "N/A")
    st.metric("Animal", animal)
    st.metric("Lugar", lugar)

    historia = generar_historia(animal, lugar)
    st.subheader("📖 Historia")
    st.write(historia)

    st.subheader("🎧 Escuchar la historia")
    reproducir_audio(historia)

    st.subheader("🖼️ Imagen Generada")
    obtener_imagen(animal, lugar)

else:
    st.info("Presiona el botón para obtener los datos actuales desde el ESP32.")
