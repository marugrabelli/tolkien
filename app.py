import streamlit as st
from google import genai
from google.types import GenerateContentConfig

# Configuración de la página de Streamlit
st.set_page_config(page_title="Tolkien Chatbot", page_icon="🧝‍♂️", layout="centered")
st.title("Tolkien AI Engineer Project 📚")
st.subheader("Chatbot especializado en el Legendarium")

# Inicializar el cliente de Gemini (busca automáticamente la variable de entorno GEMINI_API_KEY)
# Para desarrollo local rápido, puedes usar st.secrets o cargarla directamente de los componentes de Streamlit
api_key = st.sidebar.text_input("Ingresa tu Gemini API Key:", type="password")

SYSTEM_PROMPT = """
[PEGA AQUÍ EL PROMPT AVANZADO DE SISTEMA MOSTRADO ARRIBA]
"""

if api_key:
    client = genai.Client(api_key=api_key)
    
    # Configuración del modelo con el System Prompt incorporado
    config = GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        temperature=0.7,
    )

    # Inicializar el historial de chat en la sesión si no existe
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Mostrar los mensajes anteriores del chat
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Entrada del usuario
    if user_input := st.chat_input("Pregúntame sobre la Tierra Media..."):
        # Mostrar mensaje del usuario
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Generar respuesta de la IA
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            
            # Reconstruir el historial en el formato que requiere la API
            # Para mantener la memoria de la conversación de forma simple:
            contents = []
            for m in st.session_state.messages:
                contents.append(m["content"]) # Simplificado para el paso de contenido secuencial
            
            try:
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=user_input, # Para mantenerlo simple e independiente por consulta o mapear el historial estructurado
                    config=config
                )
                full_response = response.text
                message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            except Exception as e:
                st.error(f"Error al generar contenido: {e}")
else:
    st.info("Por favor, introduce tu API Key de Gemini en la barra lateral para comenzar. Es gratuita en Google AI Studio.")
