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
    st.session_state.trigger_activated = False
    st.session_state.last_trigger_word = ""
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
if "human_takeover" not in st.session_state:
    st.session_state.human_takeover = False
if "trigger_activated" not in st.session_state:
    st.session_state.trigger_activated = False
if "last_trigger_word" not in st.session_state:
    st.session_state.last_trigger_word = ""

# 5. Función de Procesamiento y Persistencia (CSV + Webhook)
def procesar_alerta_hitl(nombre, correo, telefono, palabra_trigger, context_history):
    hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # A) Persistencia local en Base de Datos CSV
    nueva_fila = {
        "Fecha_Hora": [hora_actual],
        "Nombre": [nombre],
        "Correo": [correo],
        "Telefono": [telefono],
        "Palabra_Trigger": [palabra_trigger],
        "Historial_Chat": [str(context_history[-3:])]
    }
    df_nuevo = pd.DataFrame(nueva_fila)
    
    if os.path.exists(CSV_FILE_PATH):
        df_nuevo.to_csv(CSV_FILE_PATH, mode='a', header=False, index=False)
    else:
        df_nuevo.to_csv(CSV_FILE_PATH, mode='w', header=True, index=False)
        
    # B) Envío de datos enriquecidos al Webhook de Make
    if MAKE_WEBHOOK_URL:
        payload = {
            "alert_type": "HUMAN_INTERVENTION_REQUIRED",
            "timestamp": hora_actual,
            "user_name": nombre,
            "user_email": correo,
            "user_phone": telefono,
            "trigger_word": palabra_trigger,
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

        # Renderizar historial activo en pantalla
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # FLUJO HITL ACTIVADO: Solicitud de datos por palabra crítica
        if st.session_state.trigger_activated:
            st.warning("⚠️ Ein menschlicher Experte wird benötigt / Se requiere un experto humano.")
            
            # Formulario condicional: Solo aparece tras nombrar una palabra crítica
            with st.form("formulario_contacto_urgente"):
                st.write("Por favor, dejanos tus datos para que un especialista se contacte directamente contigo:")
                form_nombre = st.text_input("Nombre Completo:")
                form_correo = st.text_input("Correo Electrónico:")
                form_telefono = st.text_input("Teléfono de Contacto:")
                form_submit = st.form_submit_with_button_coordinates("Solicitar Asistencia Humana")
                
                if form_submit:
                    if form_nombre and form_correo and form_telefono:
                        # Guardar en CSV, enviar Webhook y pasar el control al operador humano
                        procesar_alerta_hitl(form_nombre, form_correo, form_telefono, st.session_state.last_trigger_word, [m["content"] for m in st.session_state.messages])
                        st.session_state.trigger_activated = False
                        st.session_state.human_takeover = True
                        st.rerun()
                    else:
                        st.error("Todos los campos son necesarios para procesar tu solicitud de soporte.")
                        
        # ESTADO: Esperando respuesta del operador humano desde la consola
        elif st.session_state.human_takeover:
            st.info("💡 Un especialista ha sido notificado por correo electrónico. La IA permanece pausada.")
            with st.expander("🛠️ Panel de Operador Humano (Resolución)", expanded=True):
                human_response = st.text_area("Escribe la respuesta experta para el usuario:")
                if st.button("Enviar respuesta y restablecer servicio"):
                    if human_response:
                        st.session_state.messages.append({"role": "assistant", "content": f"🧔 [Menschlicher Experte]: {human_response}"})
                        st.session_state.human_takeover = False
                        st.rerun()
                        
        # ESTADO NORMAL: Chat libre con la IA
        else:
            if user_input := st.chat_input("Frag mich etwas über Mittelerde..."):
                with st.chat_message("user"):
                    st.markdown(user_input)
                st.session_state.messages.append({"role": "user", "content": user_input})

                # Validación predictiva de triggers críticos
                criterios_criticos = ["humano", "human", "mensch", "soporte", "error", "reclamación", "copyright"]
                if any(word in user_input.lower() for word in criterios_criticos):
                    st.session_state.trigger_activated = True
                    st.session_state.last_trigger_word = user_input
                    st.rerun()

                # Consumo básico del LLM
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
