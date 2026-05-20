import streamlit as st
from google import genai
import requests
import pandas as pd
from datetime import datetime
import os
import threading
import re

# 1. Configuración de la interfaz de Streamlit
st.set_page_config(page_title="Tolkien AI Hub", page_icon="🧙‍♂️", layout="centered")
st.title("LOTR 🧙‍♂️")
st.subheader("Chatbot für Dr. Rulitos")

CSV_FILE_PATH = "consultas_criticas.csv"

# --- MEJORA: COMPONENTE DE DESCARGA EN LA BARRA LATERAL ---
if os.path.exists(CSV_FILE_PATH):
    with open(CSV_FILE_PATH, "rb") as file:
        st.sidebar.download_button(
            label="📥 Descargar Base de Datos (CSV)",
            data=file,
            file_name="consultas_criticas.csv",
            mime="text/csv"
        )

# Botón lateral para reiniciar la sesión de pruebas limpiamente
if st.sidebar.button("🔄 Reiniciar Conversación"):
    st.session_state.messages = []
    st.session_state.trigger_activated = False
    st.session_state.form_submitted = False
    st.session_state.last_trigger_word = ""
    st.rerun()

# 2. Gestión de Credenciales Seguras
if "Gemini_API_key" in st.secrets:
    api_key = st.secrets["Gemini_API_key"]
elif "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    api_key = st.sidebar.text_input("Ingresa tu Gemini API Key:", type="password")

MAKE_WEBHOOK_URL = st.secrets.get("MAKE_WEBHOOK_URL", "")

# 3. Prompt del Sistema
SYSTEM_PROMPT = """
Eres J.R.R. Tolkien Bot, un motor de inteligencia artificial especializado en el Legendarium. 

### REGLA ESTRICTA DE IDIOMA Y SALUDO
- Debes responder SIEMPRE en idioma Alemán (Deutsch).
- ÚNICAMENTE cambiarás el idioma si el usuario te lo pide explícitamente ("Responde en español").
- Cada interacción DEBE comenzar con: "Mae govannen! Ich bin der Tolkien-Bot. Wie kann ich dir heute im Legendarium helfen?".
"""

# 4. Inicialización del Estado de la Aplicación
if "messages" not in st.session_state:
    st.session_state.messages = []
if "trigger_activated" not in st.session_state:
    st.session_state.trigger_activated = False
if "form_submitted" not in st.session_state:
    st.session_state.form_submitted = False
if "last_trigger_word" not in st.session_state:
    st.session_state.last_trigger_word = ""

# 5. Función de Almacenamiento y Notificación Asíncrona (Background Worker)
def _background_logging_and_alerting(nombre, correo, telefono, palabra_trigger, context_history, webhook_url, csv_path):
    hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    historial_str = str(context_history)
    
    # A) Persistencia local automática en Base de Datos CSV
    nueva_fila = {
        "Fecha_Hora": [hora_actual],
        "Nombre": [nombre],
        "Correo": [correo],
        "Telefono": [telefono],
        "Ultima_Consulta": [palabra_trigger],
        "Historial_Contexto": [historial_str]
    }
    df_nuevo = pd.DataFrame(nueva_fila)
    
    if os.path.exists(csv_path):
        df_nuevo.to_csv(csv_path, mode='a', header=False, index=False)
    else:
        df_nuevo.to_csv(csv_path, mode='w', header=True, index=False)
        
    # B) Envío de datos estructurados para el Webhook de Make
    if webhook_url:
        payload = {
            "alert_type": "HUMAN_INTERVENTION_REQUIRED",
            "timestamp": hora_actual,
            "user_name": nombre,
            "user_email": correo,
            "user_phone": telefono,
            "last_query": palabra_trigger,
            "chat_history": context_history[:-1] if len(context_history) > 1 else ["No hay mensajes previos."]
        }
        try:
            requests.post(webhook_url, json=payload, timeout=4.0)
        except Exception:
            pass

def procesar_alerta_hitl(nombre, correo, telefono, palabra_trigger, context_history):
    worker = threading.Thread(
        target=_background_logging_and_alerting,
        args=(nombre, correo, telefono, palabra_trigger, context_history, MAKE_WEBHOOK_URL, CSV_FILE_PATH)
    )
    worker.start()

# 6. Lógica de Ejecución del Chat
if api_key:
    try:
        client = genai.Client(api_key=api_key)

        # Renderizar historial activo en pantalla
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # ESTADO C: Formulario enviado (Fin del flujo del bot)
        if st.session_state.form_submitted:
            st.success("📩 Tus datos han sido registrados con éxito.")
            st.info("👋 Un asesor humano revisará tu última consulta y se pondrá en contacto directo contigo a la brevedad por teléfono o correo electrónico.")

        # ESTADO B: Palabra crítica detectada -> Formulario de datos de contacto
        elif st.session_state.trigger_activated:
            st.warning("⚠️ Servicio automatizado pausado. Se requiere asistencia de un especialista.")
            
            with st.form("formulario_contacto_urgente"):
                st.write("Por favor, completá tus datos para recibir atención personalizada de un operador:")
                form_nombre = st.text_input("Nombre Completo:")
                form_correo = st.text_input("Correo Electrónico:")
                form_telefono = st.text_input("Teléfono de Contacto:")
                form_submit = st.form_submit_button("Enviar solicitud de contacto")
                
                if form_submit:
                    if form_nombre and form_correo and form_telefono:
                        historial_completo = [m["content"] for m in st.session_state.messages]
                        
                        # Ejecutar persistencia en CSV y enviar Webhook en segundo plano
                        procesar_alerta_hitl(form_nombre, form_correo, form_telefono, st.session_state.last_trigger_word, historial_completo)
                        
                        st.session_state.trigger_activated = False
                        st.session_state.form_submitted = True
                        st.rerun()
                    else:
                        st.error("Todos los campos son obligatorios para procesar la solicitud.")
                        
        # ESTADO A: Chat normal libre con la IA
        else:
            if user_input := st.chat_input("Frag mich etwas über Mittelerde..."):
                with st.chat_message("user"):
                    st.markdown(user_input)
                st.session_state.messages.append({"role": "user", "content": user_input})

                # Normalización y análisis sintáctico de triggers críticos
                clean_input = re.sub(r'[^\w\s]', '', user_input.lower().strip())
                input_words = clean_input.split()
                
                criterios_criticos = {"humano", "human", "mensch", "soporte", "error", "reclamacion", "copyright"}
                if any(word in criterios_criticos for word in input_words):
                    st.session_state.trigger_activated = True
                    st.session_state.last_trigger_word = user_input
                    st.rerun()

                # Generación estándar del modelo con ventana de memoria optimizada
                with st.chat_message("assistant"):
                    historial_api = []
                    for msg in st.session_state.messages[-10:]:
                        api_role = "user" if msg["role"] == "user" else "model"
                        historial_api.append({
                            "role": api_role,
                            "parts": [{"text": msg["content"]}]
                        })

                    try:
                        response = client.models.generate_content(
                            model='gemini-1.5-flash',
                            contents=historial_api,
                            config={'system_instruction': SYSTEM_PROMPT, 'temperature': 0.7}
                        )
                        st.markdown(response.text)
                        st.session_state.messages.append({"role": "assistant", "content": response.text})
                    except Exception:
                        st.error("Der Dienst ist vorübergehend überlastet.")
                        
    except Exception as e:
        st.error(f"Error de inicialización del cliente: {e}")
else:
    st.info("Por favor, introduce tu API Key de Gemini para comenzar.")
