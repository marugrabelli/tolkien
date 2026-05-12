import streamlit as st
import os
import google.generativeai as genai
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA

# --- CONFIGURACIÓN DE INTERFAZ ---
st.set_page_config(page_title="Tolkien Hybrid Agent", page_icon="🧙‍♂️")
st.title("🧙‍♂️ Tolkiendil Hybrid-Assistent")

# --- GESTIÓN DE SEGURIDAD ---
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
else:
    st.error("⚠️ Configura la GOOGLE_API_KEY en los Secrets de Streamlit.")
    st.stop()

# --- MOTOR DE INTELIGENCIA HÍBRIDA (RAG + LLM) ---
@st.cache_resource
def configurar_agente():
    # 1. Carga y validación de la carpeta de conocimiento
    path = "./conocimiento/"
    if not os.path.exists(path):
        os.makedirs(path)
    
    # Cargamos archivos PDF y TXT
    loader = DirectoryLoader(path, glob="./*", loader_cls=PyPDFLoader)
    docs = loader.load()
    
    # 2. Fragmentación (Chunking) - Paso esencial para el análisis de texto
    # Dividimos en bloques de 1000 caracteres para mantener coherencia semántica
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    
    if docs:
        fragmentos = text_splitter.split_documents(docs)
        # 3. Creación de Base de Datos Vectorial
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=api_key)
        vectorstore = FAISS.from_documents(fragmentos, embeddings)
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    else:
        # Si no hay archivos, el agente funcionará solo con su conocimiento base
        retriever = None

    # 4. Configuración del Modelo de Lenguaje (Gemini)
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key, temperature=0.3)

    # PROMPT MAESTRO: Define el comportamiento híbrido e idioma alemán
    template = """
    Du bist ein hochspezialisierter KI-Experte für das Werk von J.R.R. Tolkien.
    Deine Aufgabe ist es, Fragen präzise und AUSSCHLIESSLICH AUF DEUTSCH zu beantworten.
    
    KONTEXT AUS DOKUMENTEN: {context}
    BENUTZERFRAGE: {question}
    
    ANWEISUNGEN:
    1. Antworte IMMER auf DEUTSCH.
    2. Priorisiere Informationen aus dem KONTEXT. Wenn du sie nutzt, nenne die Datei.
    3. Falls die Information NICHT im Kontext steht, nutze dein allgemeines Wissen, aber erwähne dies kurz.
    4. Beende jede Antwort mit einem '💡 Tolkien Fun Fact' auf Deutsch.
    """
    
    QA_PROMPT = PromptTemplate(template=template, input_variables=["context", "question"])

    if retriever:
        return RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={"prompt": QA_PROMPT},
            return_source_documents=True
        )
    else:
        return llm # Fallback directo si no hay documentos

# Inicializar motor
agente = configurar_agente()

# --- HISTORIAL DE CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- INTERACCIÓN ---
if prompt := st.chat_input("Stellen Sie Ihre Frage..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Ich durchsuche die Archive..."):
            # Lógica híbrida de respuesta
            if isinstance(agente, RetrievalQA):
                res = agente({"query": prompt})
                respuesta = res["result"]
                fuentes = res["source_documents"]
            else:
                # Respuesta solo IA si no hay archivos cargados
                respuesta = agente.invoke(f"Antworte auf Deutsch: {prompt}").content
                fuentes = []

            st.markdown(respuesta)
            
            # Mostrar fuentes para demostrar transparencia técnica
            if fuentes:
                with st.expander("Verwendete Quellen"):
                    for doc in fuentes:
                        st.caption(f"Datei: {doc.metadata.get('source')}")
            
            st.session_state.messages.append({"role": "assistant", "content": respuesta})
