import streamlit as st
import google.generativeai as genai
import os
import time

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Tolkiendil Gelehrter", page_icon="🧙‍♂️")

# --- CONEXIÓN API ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("⚠️ Configura GOOGLE_API_KEY en los Secrets de Streamlit.")
    st.stop()

# --- GESTIÓN DE BIBLIOTECA (RAG NATIVO) ---
@st.cache_resource
def inicializar_biblioteca():
    """Sube los libros a Google para que la IA los lea sin colapsar Streamlit."""
    documentos_subidos = []
    ruta_carpeta = "conocimiento"
    
    if os.path.exists(ruta_carpeta):
        archivos = [f for f in os.listdir(ruta_carpeta) if f.endswith(".pdf")]
        for nombre in archivos:
            ruta_completa = os.path.join(ruta_carpeta, nombre)
            try:
                # Subida directa a la infraestructura de Google
                file_uploaded = genai.upload_file(path=ruta_completa, display_name=nombre)
                # Esperar a que el archivo sea procesado por Google
                while file_uploaded.state.name == "PROCESSING":
                    time.sleep(2)
                    file_uploaded = genai.get_file(file_uploaded.name)
                documentos_subidos.append(file_uploaded)
            except Exception as e:
                st.warning(f"No se pudo cargar {nombre}: {e}")
    return documentos_subidos

# --- INTERFAZ ---
st.title("🧙‍♂️ Tolkiendil Gelehrter")
st.subheader("Experto en la Tierra Media (Antworten auf Deutsch)")

if "biblioteca" not in st.session_state:
    with st.spinner("Sincronizando libros con el cerebro de la IA..."):
        st.session_state.biblioteca = inicializar_biblioteca()

if "messages" not in st.session_state:
    st.session_state.messages = []

# Historial
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- LÓGICA DE CHAT HÍBRIDO ---
if prompt := st.chat_input("¿Qué deseas saber sobre Tolkien?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # USAMOS 1.5-PRO: Tiene 2 millones de tokens y es más estable que Flash
            model = genai.GenerativeModel('gemini-1.5-pro')
            
            # PROMPT MAESTRO ACTUALIZADO (HÍBRIDO)
            instruccion_maestra = """
            Eres el 'Tolkiendil Gelehrter'. Tu misión es asesorar con precisión técnica.
            
            FUENTES:
            1. PRIORIDAD MÁXIMA: Usa los archivos PDF adjuntos. 
            2. CAPA 2 (COMPLEMENTO): Usa tu conocimiento nativo de Gemini si el dato no está en el PDF.
            
            REGLAS:
            - IDIOMA: Responde SIEMPRE en ALEMÁN (DEUTSCH).
            - CIERRE: Añade siempre un '💡 Tolkien Fun Fact' al final en alemán.
            """
            
            # Enviamos: Instrucción + PDFs + Pregunta
            contenido_input = [instruccion_maestra] + st.session_state.biblioteca + [prompt]
            
            response = model.generate_content(contenido_input)
            
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            st.error(f"Error de conexión: {e}. Intenta reiniciar la app.")
