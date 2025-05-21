import streamlit as st
import json
import paho.mqtt.client as mqtt
import time
from openai import OpenAI
from deep_translator import GoogleTranslator
from gtts import gTTS
import os

# MQTT Configuración
MQTT_BROKER = "broker.mqttdashboard.com"
MQTT_PORT = 1883
MQTT_TOPIC = "selector/animal"

# Estados iniciales
if 'sensor_data' not in st.session_state:
    st.session_state.sensor_data = None
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""
if 'language' not in st.session_state:
    st.session_state.language = 'es'

# MQTT - recibir datos del ESP32
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

# Historia generada por OpenAI
def generar_historia(animal, lugar, api_key, idioma_destino='es'):
    client = OpenAI(api_key=api_key)

    prompt = (
        f"Escribe una historia creativa, divertida y mágica para niños, "
        f"de al menos 3 párrafos completos, donde el protagonista sea un {animal} que vive o viaja a {lugar}. "
        f"Debe incluir una pequeña aventura o dilema y una enseñanza final. "
        f"La narrativa debe ser rica en detalles y fácil de imaginar visualmente."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Eres un narrador mágico de cuentos para niños."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.9,
            max_tokens=800
        )

        historia = response.choices[0].message.content.strip()

        if idioma_destino != 'es':
            historia = GoogleTranslator(source='auto', target=idioma_destino).translate(historia)

        return historia

    except Exception as e:
        st.error(f"No se pudo generar la historia: {e}")
        return None

# Convertir texto a voz
def convertir_a_audio(texto, idioma='es', filename='historia.mp3'):
    try:
        tts = gTTS(text=texto, lang=idioma)
        tts.save(filename)
        return filename
    except Exception as e:
        st.error(f"No se pudo convertir el texto a audio: {e}")
        return None

# UI principal
st.set_page_config(page_title="Juego Animal y Lugar", page_icon="🧸")
st.title("🐾 Juego de Aventuras Interactivas")

# Entrada de API Key y selector de idioma
st.session_state.api_key = st.text_input("🔑 Ingresa tu OpenAI API Key:", type="password")
st.session_state.language = st.selectbox("🌐 Idioma de la historia:", ['es', 'en', 'fr', 'de', 'pt'])

# Botón de obtención de datos
if st.button("📡 Obtener Lectura del ESP32"):
    with st.spinner("Esperando datos..."):
        data = get_mqtt_message()
        st.session_state.sensor_data = data

# Mostrar datos y generar historia + audio
if st.session_state.sensor_data:
    st.success("✅ Datos recibidos")
    animal = st.session_state.sensor_data.get("animal", "N/A")
    lugar = st.session_state.sensor_data.get("lugar", "N/A")

    st.metric("🐶 Animal", animal)
    st.metric("🏞 Lugar", lugar)

    if st.session_state.api_key:
        historia = generar_historia(animal, lugar, st.session_state.api_key, st.session_state.language)
        if historia:
            st.markdown("### 📖 Historia Generada")
            st.write(historia)

            # Convertir a audio
            st.markdown("### 🔊 Escucha la historia")
            archivo_audio = convertir_a_audio(historia, idioma=st.session_state.language)
            if archivo_audio:
                with open(archivo_audio, "rb") as audio_file:
                    st.audio(audio_file.read(), format="audio/mp3")
    else:
        st.warning("Por favor, ingresa tu API Key para generar la historia.")
else:
    st.info("Haz clic en el botón para recibir los datos del ESP32.")


