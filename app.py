import streamlit as st
import json
import paho.mqtt.client as mqtt
import time
from openai import OpenAI
from deep_translator import GoogleTranslator
from gtts import gTTS
import os

# Configuración inicial
st.set_page_config(page_title="Cuentacuentos Animal y Lugar", page_icon="📖", layout="wide")

# Paleta de colores
primary_color = "#FDD835"  # Amarillo
secondary_color = "#FFF9C4"  # Amarillo claro
accent_color = "#FFD600"  # Amarillo fuerte

st.markdown(f"""
    <style>
        .stApp {{
            background-color: {secondary_color};
            font-family: 'Comic Sans MS', cursive, sans-serif;
        }}
        .title-container {{
            text-align: center;
            background-color: {primary_color};
            padding: 1rem;
            border-radius: 12px;
            box-shadow: 0px 4px 12px rgba(0,0,0,0.1);
        }}
        .story-box {{
            background-color: #fffbea;
            padding: 1.5rem;
            border-radius: 16px;
            box-shadow: 0px 4px 10px rgba(0,0,0,0.05);
        }}
        .metric-box {{
            background-color: #fffde7;
            padding: 1rem;
            border-radius: 12px;
            margin-bottom: 1rem;
            text-align: center;
        }}
    </style>
""", unsafe_allow_html=True)

# Estados iniciales
if 'sensor_data' not in st.session_state:
    st.session_state.sensor_data = None
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""
if 'language' not in st.session_state:
    st.session_state.language = 'es'

# MQTT Configuración
MQTT_BROKER = "broker.mqttdashboard.com"
MQTT_PORT = 1883
MQTT_TOPIC = "selector/animal"

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

def convertir_a_audio(texto, idioma='es', filename='historia.mp3'):
    try:
        tts = gTTS(text=texto, lang=idioma)
        tts.save(filename)
        return filename
    except Exception as e:
        st.error(f"No se pudo convertir el texto a audio: {e}")
        return None

# 🎛 Sidebar para la API Key y el idioma
with st.sidebar:
    st.header("🔧 Configuración")
    st.session_state.api_key = st.text_input("🔑 OpenAI API Key:", type="password")
    st.session_state.language = st.selectbox("🌐 Idioma:", ['es', 'en', 'fr', 'de', 'pt'])

# 🧩 Cabecera
st.markdown(f"<div class='title-container'><h1>✨ Cuentacuentos Animal y Lugar 🧸</h1></div>", unsafe_allow_html=True)
st.write("¡Gira la ruleta y descubre una historia mágica con tu animal favorito en un lugar inesperado!")

# 📡 Botón para recibir datos
if st.button("🎲 Obtener combinación mágica del ESP32"):
    with st.spinner("Esperando datos mágicos del universo..."):
        data = get_mqtt_message()
        st.session_state.sensor_data = data

# 📝 Mostrar datos y generar historia
if st.session_state.sensor_data:
    animal = st.session_state.sensor_data.get("animal", "N/A")
    lugar = st.session_state.sensor_data.get("lugar", "N/A")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<div class='metric-box'>🐾 <h3>Animal:</h3> <h2>{}</h2></div>".format(animal), unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='metric-box'>🏞 <h3>Lugar:</h3> <h2>{}</h2></div>".format(lugar), unsafe_allow_html=True)

    if st.session_state.api_key:
        historia = generar_historia(animal, lugar, st.session_state.api_key, st.session_state.language)
        if historia:
            st.markdown("<div class='story-box'>", unsafe_allow_html=True)
            st.markdown("### 📖 Historia mágica")
            st.write(historia)
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("### 🔊 ¡Escucha la historia contada!")
            archivo_audio = convertir_a_audio(historia, idioma=st.session_state.language)
            if archivo_audio:
                with open(archivo_audio, "rb") as audio_file:
                    st.audio(audio_file.read(), format="audio/mp3")
    else:
        st.warning("Por favor ingresa tu API Key en el panel lateral para comenzar.")
else:
    st.info("Presiona el botón para recibir una nueva historia del ESP32.")
