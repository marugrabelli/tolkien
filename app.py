import streamlit as st
import google.generativeai as genai
import os

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Tolkiendil Gelehrter", page_icon="🧙‍♂️")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("⚠️ Configura GOOGLE_API_KEY en Secrets.")
    st.stop()

# --- 2. SINCRONIZACIÓN NATIVA ---
@st.cache_resource
def sincronizar_biblioteca():
    documentos_ia = []
    ruta_conocimiento = "conocimiento"
    if os.path.exists(ruta_conocimiento):
        archivos = [f for f in os.listdir(ruta_conocimiento) if f.endswith(".pdf")]
        for nombre_archivo in archivos:
            ruta_completa = os.path.join(ruta_conocimiento, nombre_archivo)
            # Subida a Google
            archivo_subido = genai.upload_file(path=ruta_completa, display_name=nombre_archivo)
            documentos_ia.append(archivo_subido)
    return documentos_ia

# --- 3. INICIO ---
st.title("🧙‍♂️ Tolkiendil Gelehrter")

if "biblioteca" not in st.session_state:
    with st.spinner("Sincronizando libros..."):
        st.session_state.biblioteca = sincronizar_biblioteca()

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 4. LÓGICA DE RESPUESTA ---
if prompt := st.chat_input("Escribe tu duda sobre la Tierra Media..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # CAMBIO CLAVE: Usamos 'models/gemini-1.5-flash-latest' para mayor compatibilidad
            model = genai.GenerativeModel(model_name='gemini-1.5-flash-latest')
            
            instruccion_maestra = """
            Eres el 'Tolkiendil Gelehrter'. 
            PRIORIDAD 1: PDF adjuntos. 
            PRIORIDAD 2: Conocimiento nativo de Gemini.
            REGLAS: Responder SIEMPRE en ALEMÁN y añadir un '💡 Tolkien Fun Fact' al final.
            """

            contenidos = [instruccion_maestra] + st.session_state.biblioteca + [prompt]
            
            # Generamos contenido (sin forzar v1beta manualmente)
            response = model.generate_content(contenidos)
            
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            # Diagnóstico detallado si vuelve a fallar
            st.error(f"Error de conexión con el modelo: {e}")
