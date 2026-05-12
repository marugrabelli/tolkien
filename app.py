import streamlit as st
import os
import subprocess
import sys

# --- SOLUCIÓN TÉCNICA DE EMERGENCIA ---
# Si Streamlit falla en leer el requirements.txt, este bloque fuerza la instalación.
def install_package(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    import langchain
    from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
    from langchain_community.vectorstores import FAISS
    from langchain.chains import RetrievalQA
    from langchain.prompts import PromptTemplate
except ImportError:
    with st.spinner("🔧 Configurando entorno de IA por primera vez..."):
        install_package("langchain")
        install_package("langchain-google-genai")
        install_package("langchain-community")
        install_package("faiss-cpu")
        install_package("PyPDF2")
        st.rerun()

import google.generativeai as genai

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Tolkien Hybrid Expert", page_icon="🧙‍♂️")
st.title("🧙‍♂️ Tolkiendil Hybrid-Asistent")

if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
else:
    st.error("⚠️ Configura la GOOGLE_API_KEY en los Secrets.")
    st.stop()

# --- MOTOR HÍBRIDO RAG ---
@st.cache_resource
def configurar_agente():
    path = "./conocimiento/"
    if not os.path.exists(path):
        os.makedirs(path)
    
    loader = DirectoryLoader(path, glob="./*.pdf", loader_cls=PyPDFLoader)
    docs = loader.load()
    
    # Fragmentación (Paso 1: Chunking)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    
    if docs:
        fragmentos = text_splitter.split_documents(docs)
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=api_key)
        vectorstore = FAISS.from_documents(fragmentos, embeddings)
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    else:
        retriever = None

    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key, temperature=0.3)

    # Prompt Maestro en Alemán (Híbrido)
    template = """
    Du bist ein Experte für J.R.R. Tolkien. Antworte IMMER auf DEUTSCH.
    KONTEXT AUS DOKUMENTEN: {context}
    BENUTZERFRAGE: {question}
    
    REGELN:
    1. Antworte IMMER auf DEUTSCH.
    2. Priorisiere den KONTEXT und nenne die Datei.
    3. Falls nicht im Kontext, nutze dein Wissen auf Deutsch.
    4. Ende: '💡 Tolkien Fun Fact' (Deutsch).
    """
    
    QA_PROMPT = PromptTemplate(template=template, input_variables=["context", "question"])

    if retriever:
        return RetrievalQA.from_chain_type(
            llm=llm, retriever=retriever, chain_type_kwargs={"prompt": QA_PROMPT}, return_source_documents=True
        )
    return llm

agente = configurar_agente()

# --- INTERFAZ ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("Ihre Frage..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analyse..."):
            if isinstance(agente, RetrievalQA):
                res = agente({"query": prompt})
                respuesta = res["result"]
                fuentes = res["source_documents"]
            else:
                respuesta = agente.invoke(f"Antworte auf Deutsch: {prompt}").content
                fuentes = []

            st.markdown(respuesta)
            if fuentes:
                with st.expander("Quellen"):
                    for doc in fuentes:
                        st.caption(f"Datei: {doc.metadata.get('source')}")
            
            st.session_state.messages.append({"role": "assistant", "content": respuesta})
