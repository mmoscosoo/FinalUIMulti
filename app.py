import streamlit as st
import json
import paho.mqtt.client as mqtt
import time
from openai import OpenAI
from gtts import gTTS
from tempfile import NamedTemporaryFile

# 🌟 Estilo de la interfaz
st.set_page_config(page_title="Cuentacuentos Mágico", page_icon="📚", layout="centered")

# 🎨 Estilos personalizados con CSS mágico
st.markdown("""
    <style>
    .stApp {
        background-color: #fff8dc;
        color: #4b3200;
        font-family: 'Comic Sans MS', cursive, sans-serif;
    }
    .stButton>button {
        background-color: #ffcf40;
        color: black;
        border-radius: 10px;
        border: 2px solid #e0a800;
    }
    .stButton>button:hover {
        background-color: #ffe066;
        color: black;
    }
    .css-1d391kg {
        background-color: #fff8dc;
    }
    </style>
""", unsafe_allow_html=True)

# 📡 MQTT settings
MQTT_BROKER = "broker.mqttdashboard.com"
MQTT_PORT = 1883
MQTT_TOPIC = "selector/animal"

if 'sensor_data' not in st.session_state:
    st.session_state.sensor_data = None

# 🔐 Sidebar para API Key
st.sidebar.title("🔑 Configuración mágica")
api_key = st.sidebar.text_input("Introduce tu OpenAI API Key:", type="password")
st.sidebar.markdown("Esta clave permite generar cuentos, imágenes y voz 🪄")

# 📡 Función MQTT
def get_mqtt_message():
    message_received = {"received": False, "payload": None}

    def on_message(client, userdata, message):
        try:
            payload = json.loads(message.payload.decode())
            message_received["payload"] = payload
            message_received["received"] = True
        except Exception as e:
            st.error(f"Error en mensaje: {e}")
    
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
        st.error(f"Error al conectar con MQTT: {e}")
        return None

# 🤖 Generar historia
def generar_historia(animal, lugar, api_key, idioma="es"):
    try:
        client = OpenAI(api_key=api_key)
        prompt = f"Escribe un cuento largo, de al menos un párrafo completo, protagonizado por un {animal} que vive una aventura en {lugar}. Usa un tono infantil, mágico y encantador."
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8
        )
        historia = response.choices[0].message.content

        if idioma != "es":
            trad_prompt = f"Traduce el siguiente cuento al idioma {idioma}:\n\n{historia}"
            traduccion = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": trad_prompt}]
            )
            historia = traduccion.choices[0].message.content

        return historia
    except Exception as e:
        st.error(f"No se pudo generar la historia: {e}")
        return None

# 🖼️ Generar imagen con DALL·E
def generar_imagen_con_ia(animal, lugar, api_key):
    try:
        client = OpenAI(api_key=api_key)
        prompt = f"Ilustración infantil de un {animal} en {lugar}, estilo cuento de hadas, colores cálidos y detalles encantadores"
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        return response.data[0].url
    except Exception as e:
        st.error(f"No se pudo generar la imagen: {e}")
        return None

# 🔊 Texto a voz
def texto_a_audio(texto, idioma="es"):
    try:
        tts = gTTS(text=texto, lang=idioma)
        temp_file = NamedTemporaryFile(delete=False, suffix=".mp3")
        tts.save(temp_file.name)
        return temp_file.name
    except Exception as e:
        st.error(f"No se pudo convertir a audio: {e}")
        return None

# 📖 UI principal
st.title("📚 Cuentacuentos de Animalitos Mágicos")

if st.button("🎲 Obtener Animal y Lugar"):
    with st.spinner("Esperando al animalito..."):
        data = get_mqtt_message()
        st.session_state.sensor_data = data

if st.session_state.sensor_data and api_key:
    data = st.session_state.sensor_data
    animal = data.get("animal", "unicornio")
    lugar = data.get("lugar", "bosque encantado")

    st.header("✨ La Aventura de Hoy")
    st.metric("Animalito", animal)
    st.metric("Lugar Mágico", lugar)

    idioma = st.selectbox("🌐 Idioma del cuento:", ["es", "en", "fr", "pt"])

    historia = generar_historia(animal, lugar, api_key, idioma)
    if historia:
        st.markdown("### 📜 Cuento encantado")
        st.write(historia)

        imagen_url = generar_imagen_con_ia(animal, lugar, api_key)
        if imagen_url:
            st.markdown("### 🖼️ Ilustración del cuento")
            st.image(imagen_url, use_column_width=True)

        audio_file = texto_a_audio(historia, idioma)
        if audio_file:
            st.markdown("### 🔊 Escúchalo aquí")
            st.audio(audio_file, format="audio/mp3")
else:
    st.info("Haz clic en el botón para obtener animal y lugar, y asegúrate de tener una API Key mágica en el menú lateral.")
