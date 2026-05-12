import streamlit as st
import os
import sys
import subprocess

# --- CONFIGURACIÓN DE PÁGINA (Siempre primero) ---
st.set_page_config(page_title="Tolkien Expert", page_icon="🧙‍♂️")
st.title("🧙‍♂️ Tolkiendil Assistent")

# --- FUNCIÓN DE INSTALACIÓN DINÁMICA ---
def instalar_paquetes():
    with st.spinner("Instalando dependencias en el servidor..."):
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", 
                "langchain", "langchain-google-genai", "langchain-community", "faiss-cpu", "PyPDF2"])
            st.success("✅ Instalación completada. Reiniciando...")
            st.rerun()
        except Exception as e:
            st.error(f"Error al instalar: {e}")

# --- BLOQUE DE IMPORTACIÓN PROTEGIDO ---
try:
    import google.generativeai as genai
    from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
    from langchain_community.vectorstores import FAISS
    from langchain.chains import RetrievalQA
    from langchain.prompts import PromptTemplate
except ImportError:
    st.warning("⚠️ El servidor de Streamlit no ha reconocido las librerías del archivo requirements.txt.")
    if st.button("Forzar instalación manual ahora"):
        instalar_paquetes()
    st.stop()

# --- LÓGICA DE NEGOCIO ---
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
else:
    st.error("⚠️ Configura GOOGLE_API_KEY en los Secrets.")
    st.stop()

@st.cache_resource
def setup_engine():
    path = "./conocimiento/"
    if not os.path.exists(path): os.makedirs(path)
    
    loader = DirectoryLoader(path, glob="./*.pdf", loader_cls=PyPDFLoader)
    docs = loader.load()
    
    if docs:
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = text_splitter.split_documents(docs)
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=api_key)
        vectorstore = FAISS.from_documents(splits, embeddings)
        
        return RetrievalQA.from_chain_type(
            llm=ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key, temperature=0.3),
            retriever=vectorstore.as_retriever(),
            chain_type_kwargs={"prompt": PromptTemplate(
                template="Antworte immer auf DEUTSCH. Kontext: {context} Frage: {question}",
                input_variables=["context", "question"]
            )},
            return_source_documents=True
        )
    return ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key)

agente = setup_engine()

# --- CHAT UI ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("Hacer una pregunta..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if hasattr(agente, "invoke") and not isinstance(agente, ChatGoogleGenerativeAI):
            res = agente({"query": prompt})
            respuesta = res["result"]
        else:
            respuesta = agente.invoke(f"Antworte auf Deutsch: {prompt}").content
        
        st.markdown(respuesta)
        st.session_state.messages.append({"role": "assistant", "content": respuesta})
