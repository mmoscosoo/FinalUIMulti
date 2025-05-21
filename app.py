import streamlit as st
import json
import paho.mqtt.client as mqtt
import time
from openai import OpenAI
import os
from gtts import gTTS
from tempfile import NamedTemporaryFile

# Configuración visual
st.set_page_config(page_title="Cuentacuentos Animalitos", page_icon="📚", layout="centered")

# 🎨 Estilos personalizados con colores cálidos
st.markdown("""
    <style>
    body {
        background-color: #fffbe6;
    }
    .stApp {
        background-color: #fffbe6;
        color: #5c3d00;
    }
    .block-container {
        padding: 2rem 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# 📌 MQTT config
MQTT_BROKER = "broker.mqttdashboard.com"
MQTT_PORT = 1883
MQTT_TOPIC = "selector/animal"

if 'sensor_data' not in st.session_state:
    st.session_state.sensor_data = None

# 📥 Sidebar con API key
st.sidebar.title("🔐 Configuración")
api_key = st.sidebar.text_input("Introduce tu OpenAI API Key:", type="password")
st.sidebar.markdown("Tu clave es necesaria para generar historias, imágenes y audio.")

# 📡 Obtener mensaje MQTT
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

# 🤖 Generar historia con OpenAI
def generar_historia(animal, lugar, api_key, idioma="es"):
    try:
        client = OpenAI(api_key=api_key)
        prompt = f"Escribe un cuento infantil, de al menos un párrafo, protagonizado por un {animal} que vive una aventura en {lugar}. Usa un tono mágico, tierno y divertido."
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8
        )
        historia = response.choices[0].message.content

        # Traducción si no es español
        if idioma != "es":
            prompt_trad = f"Traduce el siguiente cuento al idioma {idioma}:\n\n{historia}"
            traduccion = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt_trad}]
            )
            historia = traduccion.choices[0].message.content

        return historia
    except Exception as e:
        st.error(f"No se pudo generar la historia:\n\n{e}")
        return None

# 🖼️ Generar imagen con DALL·E
def generar_imagen_con_ia(animal, lugar, api_key):
    try:
        client = OpenAI(api_key=api_key)
        prompt = f"Un {animal} en {lugar}, estilo cuento infantil, ilustración colorida, amigable y mágica"
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        image_url = response.data[0].url
        return image_url
    except Exception as e:
        st.error(f"No se pudo generar la imagen: {e}")
        return None

# 🔊 Convertir texto a voz
def texto_a_audio(texto, idioma="es"):
    try:
        tts = gTTS(text=texto, lang=idioma)
        temp_file = NamedTemporaryFile(delete=False, suffix=".mp3")
        tts.save(temp_file.name)
        return temp_file.name
    except Exception as e:
        st.error(f"No se pudo generar el audio: {e}")
        return None

# Título principal
st.title("📖 Cuentacuentos de Animalitos Mágicos")

# Obtener datos del ESP32
if st.button("🎲 Obtener Animal y Lugar"):
    with st.spinner("Esperando datos mágicos del ESP32..."):
        data = get_mqtt_message()
        st.session_state.sensor_data = data

# Mostrar resultados
if st.session_state.sensor_data and api_key:
    data = st.session_state.sensor_data
    animal = data.get("animal", "unicornio")
    lugar = data.get("lugar", "bosque encantado")

    st.header("✨ Aventura de Hoy")
    st.metric("Animal", animal)
    st.metric("Lugar", lugar)

    idioma = st.selectbox("🌐 ¿En qué idioma quieres escuchar el cuento?", ["es", "en", "fr", "pt"])

    historia = generar_historia(animal, lugar, api_key, idioma)
    if historia:
        st.markdown("### 📚 Cuento generado")
        st.write(historia)

        # Mostrar imagen IA
        st.markdown("### 🎨 Ilustración mágica")
        imagen_url = generar_imagen_con_ia(animal, lugar, api_key)
        if imagen_url:
            st.image(imagen_url, use_column_width=True)

        # Audio
        audio_file = texto_a_audio(historia, idioma)
        if audio_file:
            st.markdown("### 🔊 Escucha el cuento")
            st.audio(audio_file, format="audio/mp3")
else:
    st.info("Haz clic en el botón para obtener una lectura y asegúrate de ingresar tu API Key en el menú lateral.")

