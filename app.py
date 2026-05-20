import streamlit as st
from google import genai
import requests

# 1. Configuración de la interfaz de Streamlit
st.set_page_config(page_title="Tolkien AI Hub", page_icon="🧙‍♂️", layout="centered")
st.title("LOTR 🧙‍♂️")
st.subheader("Chatbot für Dr. Rulitos")

# 2. Gestión de Credenciales Seguras (Soporta minúsculas y mayúsculas según tus secrets)
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
elif "Gemini_API_key" in st.secrets:
    api_key = st.secrets["Gemini_API_key"]
else:
    api_key = st.sidebar.text_input("Ingresa tu Gemini API Key:", type="password")

# Captura de la URL de automatización de Make desde tus secrets
MAKE_WEBHOOK_URL = st.secrets.get("MAKE_WEBHOOK_URL", "")

# 3. Prompt del Sistema (Core de Conocimiento Fijo)
SYSTEM_PROMPT = """
Eres J.R.R. Tolkien Bot, un motor de inteligencia artificial especializado en el Legendarium. 

### REGLA ESTRICTA DE IDIOMA Y SALUDO
- Debes responder SIEMPRE en idioma Alemán (Deutsch).
- ÚNICAMENTE cambiarás el idioma si el usuario te lo pide explícitamente ("Responde en español").
- Cada interacción DEBE comenzar con: "Mae govannen! Ich bin der Tolkien-Bot. Wie kann ich dir heute im Legendarium helfen?".

### ARQUITECTURA DE RESPUESTA
- Canon Literario: Basado en libros (Silmarillion, LOTR, Historia de la Tierra Media).
- Foros/Comunidad: Menciona debates sobre temas ambiguos.
- Fun Fact: Añade siempre un dato biográfico o lingüístico al final.
"""

# 4. Inicialización del Estado de la Aplicación (Memoria e HITL)
if "messages" not in st.session_state:
    st.session_state.messages = []
if "human_takeover" not in st.session_state:
    st.session_state.human_takeover = False

# 5. Función de Alerta Externa hacia el Webhook de Make
def trigger_human_intervention(user_text, context_history):
    if MAKE_WEBHOOK_URL:
        payload = {
            "alert_type": "HUMAN_INTERVENTION_REQUIRED",
            "trigger_word": user_text,
            "chat_snippet": context_history[-3:] if len(context_history) >= 3 else context_history
        }
        try:
            requests.post(MAKE_WEBHOOK_URL, json=payload, timeout=5)
        except Exception:
            pass

# 6. Lógica de Ejecución del Chat
if api_key:
    try:
        client = genai.Client(api_key=api_key)

        # Mostrar historial de conversación retenido en la sesión
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # CONTROL DEL ESTADO DE INTERVENCIÓN HUMANA (Human-in-the-Loop)
        if st.session_state.human_takeover:
            st.warning("⚠️ Ein menschlicher Experte überprüft dieses Ticket. Die KI ist vorübergehend pausiert.")
            st.info("💡 Un especialista ha sido notificado mediante el sistema de alertas por correo. El bot se encuentra en pausa.")
            
            # Panel administrativo embebido para simular la resolución del operador humano
            with st.expander("🛠️ Panel de Operador Humano (Resolución de Incidencias)"):
                human_response = st.text_area("Escribe la respuesta experta para el usuario:")
                if st.button("Enviar respuesta y restablecer servicio"):
                    if human_response:
                        st.session_state.messages.append({"role": "assistant", "content": f"🧔 [Menschlicher Experte]: {human_response}"})
                        st.session_state.human_takeover = False
                        st.rerun()
        else:
            # Entrada de texto del usuario
            if user_input := st.chat_input("Frag mich etwas über Mittelerde..."):
                with st.chat_message("user"):
                    st.markdown(user_input)
                st.session_state.messages.append({"role": "user", "content": user_input})

                # INTERCEPCIÓN PREVIA: Criterios HITL de detección de palabras clave críticas
                criterios_criticos = ["humano", "human", "mensch", "soporte", "error", "reclamación", "copyright"]
                if any(word in user_input.lower() for word in criterios_criticos):
                    st.session_state.human_takeover = True
                    trigger_human_intervention(user_input, [m["content"] for m in st.session_state.messages])
                    st.rerun()

                # GENERACIÓN DE CONTENIDO CON MEMORIA REAL DE CONTEXTO
                with st.chat_message("assistant"):
                    # Formatear el historial completo de la sesión para el SDK de Gemini
                    historial_api = []
                    for msg in st.session_state.messages:
                        api_role = "user" if msg["role"] == "user" else "model"
                        historial_api.append({
                            "role": api_role,
                            "parts": [{"text": msg["content"]}]
                        })

                    try:
                        response = client.models.generate_content(
                            model='gemini-1.5-flash',  # Modelo de producción estable sin error 503
                            contents=historial_api,    # Pasamos el historial completo estructurado
                            config={
                                'system_instruction': SYSTEM_PROMPT,
                                'temperature': 0.7
                            }
                        )
                        st.markdown(response.text)
                        st.session_state.messages.append({"role": "assistant", "content": response.text})
                    except Exception as e:
                        st.error("Der Dienst ist vorübergehend überlastet. Bitte versuchen Sie es gleich noch einmal.")
                        
    except Exception as e:
        st.error(f"Error de inicialización del cliente: {e}")
else:
    st.info("Por favor, introduce tu API Key de Gemini para comenzar.")
