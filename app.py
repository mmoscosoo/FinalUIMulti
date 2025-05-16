import streamlit as st
import json
import paho.mqtt.client as mqtt
import time

MQTT_BROKER = "broker.mqttdashboard.com"
MQTT_PORT = 1883
MQTT_TOPIC = "selector/animal"

# Variables de estado para los datos del sensor
if 'sensor_data' not in st.session_state:
    st.session_state.sensor_data = None

def get_mqtt_message():
    """Función para obtener un único mensaje MQTT"""
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

# Interfaz Streamlit para animal y lugar
st.set_page_config(page_title="Animal y Lugar", page_icon="🌍")
st.title("Visualizador de Animal y Lugar")

if st.button("Obtener Lectura del ESP32"):
    with st.spinner("Esperando datos..."):
        data = get_mqtt_message()
        st.session_state.sensor_data = data

if st.session_state.sensor_data:
    st.success("Datos recibidos correctamente")
    st.metric("Animal", st.session_state.sensor_data.get("animal", "N/A"))
    st.metric("Valor Animal", st.session_state.sensor_data.get("valorAnimal", "N/A"))
    st.metric("Lugar", st.session_state.sensor_data.get("lugar", "N/A"))
    st.metric("Valor Lugar", st.session_state.sensor_data.get("valorLugar", "N/A"))
else:
    st.info("Presiona el botón para obtener los datos actuales desde el ESP32.")
