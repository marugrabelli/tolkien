import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import os

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Tolkien AI - Deutsch", layout="wide")

# Validación de Key
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⚠️ Falta la clave en Secrets.")
    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# --- LECTURA OPTIMIZADA (Caché persistente) ---
@st.cache_data(show_spinner=False)
def cargar_biblioteca_masiva():
    texto_total = ""
    ruta_carpeta = "conocimiento"
    if not os.path.exists(ruta_carpeta):
        return ""
    
    archivos = [f for f in os.listdir(ruta_carpeta) if f.endswith(".pdf")]
    
    # Barra de progreso para grandes volúmenes
    progreso = st.progress(0)
    for i, archivo in enumerate(archivos):
        try:
            reader = PdfReader(os.path.join(ruta_carpeta, archivo))
            for page in reader.pages:
                # Extraemos solo texto esencial para ahorrar memoria
                content = page.extract_text()
                if content:
                    texto_total += content + " "
        except Exception as e:
            print(f"Error en {archivo}: {e}")
        
        progreso.progress((i + 1) / len(archivos))
    
    return texto_total

# --- INTERFAZ ---
st.title("🧙‍♂️ Agent Tolkien (Respuesta en Alemán)")

# Carga de datos con caché para que solo "le cueste" la primera vez
if "conocimiento" not in st.session_state:
    with st.spinner("Procesando gran volumen de datos... Esto solo ocurre una vez."):
        st.session_state.conocimiento = cargar_biblioteca_masiva()

if not st.session_state.conocimiento:
    st.warning("Carpeta /conocimiento vacía.")
    st.stop()

# Historial de Chat
if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- LÓGICA DEL CHAT ---
if prompt := st.chat_input("Pregunta en español, responderé en alemán..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Contexto limitado para evitar errores de saturación (Tokens)
            # Usamos los primeros 30k caracteres como base de conocimiento relevante
            contexto_ia = f"""
            Eres un experto en el universo de J.R.R. Tolkien.
            BASE DE CONOCIMIENTO (Libros): {st.session_state.conocimiento[:30000]}
            
            INSTRUCCIÓN:
            1. Analiza la pregunta del usuario basándote en los libros.
            2. DEBES RESPONDER SIEMPRE EN ALEMÁN (DEUTSCH).
            3. Si la respuesta no está en el texto, usa tu conocimiento general de Tolkien pero mantén el idioma alemán.
            """
            
            response = model.generate_content([contexto_ia, prompt])
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"Error: {e}")
