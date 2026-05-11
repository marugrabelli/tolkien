import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import os

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Tolkien Expert AI", page_icon="🧙‍♂️")

# Validación de Key en Secrets
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⚠️ Configura GOOGLE_API_KEY en Settings > Secrets.")
    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# --- MOTOR DE LECTURA DE BIBLIOTECA ---
@st.cache_resource
def procesar_biblioteca():
    """Lee todos los PDF cargados por el admin en la carpeta conocimiento/"""
    texto_acumulado = ""
    ruta_carpeta = "conocimiento"
    
    if os.path.exists(ruta_carpeta):
        archivos = [f for f in os.listdir(ruta_carpeta) if f.endswith(".pdf")]
        for archivo in archivos:
            try:
                reader = PdfReader(os.path.join(ruta_carpeta, archivo))
                for page in reader.pages:
                    texto_acumulado += page.extract_text() + "\n"
            except Exception as e:
                st.warning(f"Error con {archivo}: {e}")
    return texto_acumulado

# --- INTERFAZ ---
st.title("🧙‍♂️ Tolkien Knowledge Agent")
st.info("Agente experto basado en los libros oficiales (Responde en Alemán).")

# Carga de datos (Se hace una sola vez al arrancar)
with st.spinner("Sincronizando biblioteca del administrador..."):
    datos_libros = procesar_biblioteca()

if not datos_libros:
    st.error("⚠️ No hay libros cargados en la carpeta /conocimiento de GitHub.")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

# Historial
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Entrada
if prompt := st.chat_input("¿Qué deseas consultar?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Instrucción maestra: Datos en español -> Respuesta en Alemán
            contexto_ia = f"""
            Eres un experto en Tolkien. 
            DATOS DE LOS LIBROS: {datos_libros[:30000]}
            
            REGLAS:
            1. Responde ÚNICAMENTE en idioma ALEMÁN (DEUTSCH).
            2. Usa los datos proporcionados para ser preciso.
            3. Si no sabes algo, dilo en alemán.
            
            Pregunta: {prompt}
            """
            
            response = model.generate_content(contexto_ia)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"Error en la IA: {e}")
