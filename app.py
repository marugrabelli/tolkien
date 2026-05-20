import streamlit as st
from google import genai
import requests
import pandas as pd
from datetime import datetime
import os

# 1. Configuración de la interfaz de Streamlit
st.set_page_config(page_title="Tolkien AI Hub", page_icon="🧙‍♂️", layout="centered")
st.title("LOTR 🧙‍♂️")
st.subheader("Chatbot für Dr. Rulitos")

# Botón lateral para reiniciar la sesión de pruebas limpiamente
if st.sidebar.button("🔄 Reiniciar Conversación"):
    st.session_state.messages = []
    st.session_state.human_takeover = False
    st.rerun()

# 2. Gestión de Credenciales Seguras
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
elif "Gemini_API_key" in st.secrets:
    api_key = st.secrets["Gemini_API_key"]
else:
    api_key = st.sidebar.text_input("Ingresa tu Gemini API Key:", type="password")

MAKE_WEBHOOK_URL = st.secrets.get("MAKE_WEBHOOK_URL", "")
CSV_FILE_PATH = "consultas_criticas.csv"

# 3. Prompt del Sistema (Core de Conocimiento Fijo)
SYSTEM_PROMPT = """
Eres J.R.R. Tolkien Bot, un motor de inteligencia artificial especializado en el Legendarium. 

### REGLA ESTRICTA DE IDIOMA Y SALUDO
- Debes responder SIEMPRE en idioma Alemán (Deutsch).
- ÚNICAMENTE cambiarás el idioma si el usuario te lo pide explícitamente ("Responde en español").
- Cada interacción DEBE comenzar con: "Mae govannen! Ich bin der Tolkien-Bot. Wie kann ich dir heute im Legendarium helfen?".
"""

# 4. Inicialización del Estado de la Aplicación (Memoria, HITL y Datos de Usuario)
if "messages" not in st.session_state:
    st.session_state.messages = []
if "human_takeover" not in st.session_state:
    st.session_state.human_takeover = False
if "user_registered" not in st.session_state:
    st.session_state.user_registered = False

# --- PASO NUEVO: FORMULARIO DE REGISTRO PARA EL MVP ---
if not st.session_state.user_registered:
    st.info("👋 Bitte registrieren Sie sich, um den Chat zu starten / Por favor, regístrate para iniciar el chat:")
    with st.form("registro_usuario"):
        nombre = st.text_input("Nombre Completo:")
        correo = st.text_input("Correo Electrónico:")
        telefono = st.text_input("Teléfono de Contacto:")
        submit_btn = st.form_submit_with_button_coordinates("Ingresar al Chat")
        
        if submit_btn:
            if nombre and correo and telefono:
                st.session_state.user_name = nombre
                st.session_state.user_email = correo
                st.session_state.user_phone = telefono
                st.session_state.user_registered = True
                st.rerun()
            else:
                st.error("Todos los campos son obligatorios para poder asistirte en caso de soporte.")
    st.stop() # Frena la ejecución hasta que se registre

# 5. Función de Almacenamiento Local (CSV) y Alerta Externa (Webhook)
def guardar_en_csv_y_alertar(user_text, context_history):
    hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # A) Estructurar los datos para la Base de Datos CSV
    nueva_fila = {
        "Fecha_Hora": [hora_actual],
        "Nombre": [st.session_state.user_name],
        "Correo": [st.session_state.user_email],
        "Telefono": [st.session_state.user_phone],
        "Palabra_Trigger": [user_text],
        "Historial_Chat": [str(context_history[-3:])]
    }
    df_nuevo = pd.DataFrame(nueva_fila)
    
    # Si el archivo ya existe, añade la fila; si no, lo crea con cabeceras
    if os.path.exists(CSV_FILE_PATH):
        df_nuevo.to_csv(CSV_FILE_PATH, mode='a', header=False, index=False)
    else:
        df_nuevo.to_csv(CSV_FILE_PATH, mode='w', header=True, index=False)
        
    # B) Estructurar los datos enriquecidos para el Webhook de Make
    if MAKE_WEBHOOK_URL:
        payload = {
            "alert_type": "HUMAN_INTERVENTION_REQUIRED",
            "timestamp": hora_actual,
            "user_name": st.session_state.user_name,
            "user_email": st.session_state.user_email,
            "user_phone": st.session_state.user_phone,
            "trigger_word": user_text,
            "chat_snippet": context_history[-3:] if len(context_history) >= 3 else context_history
        }
        try:
            requests.post(MAKE_WEBHOOK_URL, json=payload, timeout=2.0)
        except requests.exceptions.RequestException:
            st.sidebar.error("⚠️ Alerta de red: No se pudo enviar el correo de notificación.")

# 6. Lógica de Ejecución del Chat
if api_key:
    try:
        client = genai.Client(api_key=api_key)

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # CONTROL DEL ESTADO HUMAN-IN-THE-LOOP
        if st.session_state.human_takeover:
            st.warning("⚠️ Ein menschlicher Experte überprüft dieses Ticket. Die KI ist vorübergehend pausiert.")
            st.info(f"💡 Un especialista ha sido notificado. Nos contactaremos con vos a: {st.session_state.user_phone} o {st.session_state.user_email}.")
            
            with st.expander("🛠️ Panel de Operador Humano (Resolución)", expanded=True):
                human_response = st.text_area("Escribe la respuesta experta:")
                if st.button("Enviar respuesta y restablecer servicio"):
                    if human_response:
                        st.session_state.messages.append({"role": "assistant", "content": f"🧔 [Menschlicher Experte]: {human_response}"})
                        st.session_state.human_takeover = False
                        st.rerun()
        else:
            if user_input := st.chat_input("Frag mich etwas über Mittelerde..."):
                with st.chat_message("user"):
                    st.markdown(user_input)
                st.session_state.messages.append({"role": "user", "content": user_input})

                # INTERCEPCIÓN PREVIA
                criterios_criticos = ["humano", "human", "mensch", "soporte", "error", "reclamación", "copyright"]
                if any(word in user_input.lower() for word in criterios_criticos):
                    st.session_state.human_takeover = True
                    # Ejecuta almacenamiento en CSV y dispara Webhook con datos personales
                    guardar_en_csv_y_alertar(user_input, [m["content"] for m in st.session_state.messages])
                    st.rerun()

                # GENERACIÓN DE CONTENIDO CON MEMORIA REAL
                with st.chat_message("assistant"):
                    historial_api = []
                    for msg in st.session_state.messages:
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
