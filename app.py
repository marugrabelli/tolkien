import streamlit as st
import google.generativeai as genai

# --- CONFIGURACIÓN ESTRICTA ---
st.set_page_config(page_title="Tolkien Bot")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Falta API Key")
    st.stop()

# --- PROMPT MAESTRO (Sin archivos, solo inteligencia) ---
# Si los archivos fallan, vamos a usar la potencia nativa de Gemini 
# que ya conoce a Tolkien a la perfección.
st.title("🧙‍♂️ Tolkiendil Gelehrter")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("Escribe aquí..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # CAMBIO DE MODELO A PRO 1.0 (El más estable del mundo)
            model = genai.GenerativeModel('gemini-1.0-pro')
            
            instruccion = """
            Responde SIEMPRE en ALEMÁN. 
            Eres experto en Tolkien. Usa tu base de datos interna.
            Al final añade un '💡 Tolkien Fun Fact' en alemán.
            """
            
            response = model.generate_content(f"{instruccion}\n\nPregunta: {prompt}")
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"Error crítico: {e}")
