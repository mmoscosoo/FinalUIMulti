import streamlit as st
from openai import OpenAI
from gtts import gTTS
import os
from deep_translator import GoogleTranslator

# Configura cliente OpenAI con la clave de secretos
client = OpenAI(api_key=st.secrets["openai_api_key"])

# Función para generar la historia
def generar_historia(animal, lugar):
    prompt = f"Escribe una historia corta sobre un {animal} que vive en {lugar}."

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # Usa "gpt-4" si tienes acceso
        messages=[
            {"role": "system", "content": "Eres un narrador de cuentos infantiles."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=500
    )

    historia = response.choices[0].message.content
    return historia

# Función para traducir la historia
def traducir_texto(texto, idioma_destino):
    return GoogleTranslator(source='auto', target=idioma_destino).translate(texto)

# Función para convertir texto en audio
def texto_a_audio(texto, idioma):
    tts = gTTS(text=texto, lang=idioma)
    tts.save("historia.mp3")
    return "historia.mp3"

# Interfaz de usuario
st.title("Generador de Cuentos Infantiles")

animal = st.text_input("Ingresa un animal:")
lugar = st.text_input("Ingresa un lugar:")
idioma = st.selectbox("Selecciona un idioma para la historia:", ["es", "en", "fr", "de"])

if st.button("Generar historia"):
    if animal and lugar:
        historia = generar_historia(animal, lugar)
        historia_traducida = traducir_texto(historia, idioma)
        st.markdown("### Historia:")
        st.write(historia_traducida)

        ruta_audio = texto_a_audio(historia_traducida, idioma)
        st.audio(ruta_audio)
    else:
        st.warning("Por favor, completa todos los campos.")


