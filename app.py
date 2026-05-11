import streamlit as st
import google.generativeai as genai
import os

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Tolkiendil Gelehrter", page_icon="🧙‍♂️", layout="centered")

# --- 2. CONEXIÓN CON LA API KEY ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("⚠️ Configura GOOGLE_API_KEY en los Secrets de Streamlit.")
    st.stop()

# --- 3. INYECCIÓN DE CONOCIMIENTO (RAG NATIVO) ---
@st.cache_resource
def sincronizar_biblioteca():
    """Sube los libros a la infraestructura de Google para procesamiento nativo."""
    documentos_ia = []
    ruta_conocimiento = "conocimiento"
    
    if os.path.exists(ruta_conocimiento):
        archivos = [f for f in os.listdir(ruta_conocimiento) if f.endswith(".pdf")]
        if archivos:
            for nombre_archivo in archivos:
                ruta_completa = os.path.join(ruta_conocimiento, nombre_archivo)
                # La IA procesa el archivo directamente
                archivo_subido = genai.upload_file(path=ruta_completa, display_name=nombre_archivo)
                documentos_ia.append(archivo_subido)
    return documentos_ia

# --- 4. INICIALIZACIÓN ---
st.title("🧙‍♂️ Tolkiendil Gelehrter")
st.markdown("Expertise in J.R.R. Tolkiens Welt (Antworten auf Deutsch)")

if "biblioteca" not in st.session_state:
    with st.spinner("Sincronizando biblioteca de la Tierra Media..."):
        st.session_state.biblioteca = sincronizar_biblioteca()

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 5. VISUALIZACIÓN DEL CHAT ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 6. LÓGICA DE RESPUESTA (PROMPT MAESTRO) ---
if prompt := st.chat_input("Escribe tu duda sobre la Tierra Media..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # --- PROMPT MAESTRO ACTUALIZADO ---
            instruccion_maestra = """
            Eres el 'Tolkiendil Gelehrter' (Erudito de Tolkien). Tu misión es asesorar con máxima precisión sobre el Legendarium.

            FUENTES DE INFORMACIÓN:
            1. PRIORIDAD ALTA: Utiliza los archivos PDF proporcionados. Si la respuesta está ahí, es tu fuente primaria.
            2. CAPA DE COMPLEMENTO: Si el detalle no está en los PDF, utiliza tu entrenamiento nativo sobre toda la obra de J.R.R. Tolkien (cartas, borradores, biografía).

            REGLAS INNEGOCIABLES:
            - IDIOMA: Responde SIEMPRE en ALEMÁN (DEUTSCH), sin importar el idioma de la pregunta.
            - PRECISIÓN: Diferencia entre hechos de los libros y elementos de las adaptaciones.
            - FUN FACT: Al final de cada respuesta, añade obligatoriamente una sección: '💡 Tolkien Fun Fact' con una curiosidad en alemán.
            """

            # Combinamos la instrucción, el prompt y los archivos PDF
            contenidos = [instruccion_maestra] + st.session_state.biblioteca + [prompt]
            
            response = model.generate_content(contenidos)
            
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            st.error(f"Error técnico en el servicio: {e}")
