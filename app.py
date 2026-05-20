import streamlit as st
from google import genai
import requests

# 1. Configuración de la interfaz de Streamlit
st.set_page_config(page_title="Tolkien AI Hub", page_icon="🧙‍♂️", layout="centered")
st.title("LOTR 🗺️")
st.subheader("Análisis Avanzado & Asistencia en el Legendarium")

# 2. Gestión de Credenciales Seguras
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    api_key = st.sidebar.text_input("Ingresa tu Gemini API Key:", type="password")

# URL de Webhook simulado para simular el envío a Make/Zapier (reemplazar con una URL real si se desea)
MAKE_WEBHOOK_URL = st.secrets.get("MAKE_WEBHOOK_URL", "https://hooks.make.com/simulado")

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

# 4. Inicialización del Estado de la Aplicación
if "messages" not in st.session_state:
    st.session_state.messages = []
if "human_takeover" not in st.session_state:
    st.session_state.human_takeover = False

# 5. Función de Alerta: Human-in-the-Loop (HITL)
def trigger_human_intervention(user_text, context_history):
    """Envía una alerta externa por Webhook simulando una notificación a WhatsApp/Email"""
    payload = {
        "alert_type": "HUMAN_INTERVENTION_REQUIRED",
        "trigger_word": user_text,
        "chat_snippet": context_history[-3:] if len(context_history) >= 3 else context_history
    }
    try:
        # Petición asíncrona simulada hacia la herramienta de automatización
        requests.post(MAKE_WEBHOOK_URL, json=payload, timeout=5)
    except Exception:
        pass # Evita romper la experiencia si el webhook de prueba no está activo

# 6. Lógica de Ejecución del Chat
if api_key:
    client = genai.Client(api_key=api_key)

    # Mostrar historial de conversación retenido en la sesión
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Si se activó el estado de intervención humana, bloqueamos el bot
    if st.session_state.human_takeover:
        st.warning("⚠️ Ein menschlicher Experte überprüft dieses Ticket. Die KI ist vorübergehend pausiert.")
        st.info("💡 Un especialista del Legendarium ha sido notificado por WhatsApp/Email debido a la naturaleza de tu consulta. Te contactaremos a la brevedad.")
        
        # Pestaña de administración simulada para demostrar cómo el humano interviene y guarda datos
        with st.expander("🛠️ Panel de Operador Humano (Simulación de Soporte)"):
            st.write("Como AI Engineer, aquí demostrás cómo el humano toma el control:")
            human_response = st.text_area("Escribe la respuesta experta para el usuario:")
            if st.button("Enviar respuesta y almacenar en Logs"):
                if human_response:
                    st.session_state.messages.append({"role": "assistant", "content": f"🧔 [Menschlicher Experte]: {human_response}"})
                    # Restablecer el bot tras la intervención del operador
                    st.session_state.human_takeover = False
                    st.rerun()
    else:
        # Entrada estándar del usuario
        if user_input := st.chat_input("Frag mich etwas über Mittelerde..."):
            with st.chat_message("user"):
                st.markdown(user_input)
            st.session_state.messages.append({"role": "user", "content": user_input})

            # --- EVALUACIÓN DE CRITERIOS HITL (Triggers) ---
            # Definimos palabras clave de insatisfacción o solicitudes explícitas de asistencia humana
            criterios_criticos = ["humano", "human", "mensch", "soporte", "error", "reclamación", "copyright", "malísimo"]
            
            if any(word in user_input.lower() for word in criterios_criticos):
                st.session_state.human_takeover = True
                # Disparar la automatización de notificación externa
                trigger_human_intervention(user_input, [m["content"] for m in st.session_state.messages])
                st.rerun()

            # --- OPCIÓN 1: PROCESAMIENTO CON MEMORIA DE CONTEXTO REAL ---
            with st.chat_message("assistant"):
                # Formatear todo el historial acumulado según las reglas estrictas del SDK de Gemini
                historial_api = []
                for msg in st.session_state.messages:
                    api_role = "user" if msg["role"] == "user" else "model"
                    historial_api.append({
                        "role": api_role,
                        "parts": [{"text": msg["content"]}]
                    })

                try:
                    # Se envía la secuencia completa de la conversación a la API
                    response = client.models.generate_content(
                        model='gemini-1.5-flash',
                        contents=historial_api,
                        config={
                            'system_instruction': SYSTEM_PROMPT,
                            'temperature': 0.7
                        }
                    )
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                except Exception as e:
                    st.error("Der Dienst ist vorübergehend überlastet. Bitte versuchen Sie es gleich noch einmal.")
else:
    st.info("Por favor, introduce tu API Key de Gemini para comenzar.")
