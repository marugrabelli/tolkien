import streamlit as st
import os
import google.generativeai as genai
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA

# --- CONFIGURACIÓN DE PÁGINA Y ESTILO ---
st.set_page_config(page_title="Tolkien Expert Agent", page_icon="🧙‍♂️")
st.title("🧙‍♂️ Agente Especialista en Tolkien")
st.markdown("---")

# --- VALIDACIÓN DE API KEY ---
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
else:
    st.error("⚠️ Falta la API Key en los Secrets de Streamlit.")
    st.stop()

# --- PROCESAMIENTO DE CONOCIMIENTO (LÓGICA RAG) ---
@st.cache_resource
def inicializar_agente():
    """Carga documentos, fragmenta y crea la base de datos vectorial."""
    # 1. Cargar documentos desde la carpeta 'conocimiento'
    # Intentamos cargar PDFs y TXTs
    loader_pdf = DirectoryLoader('./conocimiento/', glob="./*.pdf", loader_cls=PyPDFLoader)
    loader_txt = DirectoryLoader('./conocimiento/', glob="./*.txt", loader_cls=TextLoader)
    
    docs = loader_pdf.load() + loader_txt.load()
    
    if not docs:
        st.warning("No se encontraron documentos en la carpeta 'conocimiento'.")
        return None

    # 2. Fragmentación (Chunking) para mantener el contexto
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    fragmentos = text_splitter.split_documents(docs)

    # 3. Creación de Embeddings y Base de Datos Vectorial (FAISS)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=api_key)
    vectorstore = FAISS.from_documents(fragmentos, embeddings)
    
    # 4. Configuración del modelo de chat y la cadena de consulta
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key, temperature=0.3)
    
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
        return_source_documents=True
    )
    return qa_chain

# Inicializar el agente
agente = inicializar_agente()

# --- INTERFAZ DE CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar historial
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Entrada de usuario
if prompt := st.chat_input("Consulta a la biblioteca de Tolkien..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if agente:
            with st.spinner("Consultando archivos de conocimiento..."):
                # Ejecutar la consulta RAG
                resultado = agente({"query": prompt})
                respuesta = resultado["result"]
                fuentes = resultado["source_documents"]

                # Formatear respuesta con fuentes para LinkedIn (Demuestra rigor)
                st.markdown(respuesta)
                
                with st.expander("Ver fuentes consultadas"):
                    for doc in fuentes:
                        st.caption(f"Archivo: {doc.metadata.get('source')} - Fragmento: {doc.page_content[:200]}...")
                
                st.session_state.messages.append({"role": "assistant", "content": respuesta})
        else:
            st.error("El agente no pudo iniciarse. Verifica la carpeta 'conocimiento'.")
