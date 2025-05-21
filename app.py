import streamlit as st
import openai

st.set_page_config(page_title="Generador de Historias", layout="centered")

st.title("📚 Generador de Historias con IA")

# ✅ Input de la clave API directamente en la interfaz
api_key = st.text_input("🔐 Ingresa tu clave de API de OpenAI", type="password")

# Inputs para la historia
animal = st.text_input("🦊 Dime un animal")
lugar = st.text_input("📍 Dime un lugar")

def generar_historia(api_key, animal, lugar):
    openai.api_key = api_key
    
    prompt = f"Escribe una historia para niños protagonizada por un {animal} en {lugar}."
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperat
