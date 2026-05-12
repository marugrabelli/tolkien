import streamlit as st
import os
import google.generativeai as genai

# Importaciones corregidas y validadas para evitar el error de la línea 6
try:
    from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
    from langchain_community.vectorstores import FAISS
    from langchain.chains import RetrievalQA
    from langchain.prompts import PromptTemplate
except ImportError as e:
    st.error(f"Instalación incompleta: {e}. Revisa tu archivo requirements.txt")
    st.stop()

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Tolkien Hybrid Agent", page_icon="🧙‍♂️")
st.title("🧙‍♂️ Tolkiendil Hybrid-Assistent")

# --- SEGURIDAD ---
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
else:
    st.error("⚠️ Configura la GOOGLE_API_KEY en los Secrets de Streamlit.")
    st.stop()

# --- MOTOR HÍBRIDO (RAG + LLM) ---
@st.cache_resource
def inicializar_motor():
    path = "./conocimiento/"
    if not os.path.exists(path):
        os.makedirs(path)
    
    # Carga de documentos (PDF)
    loader = DirectoryLoader(path, glob="./*.pdf", loader_cls=PyPDFLoader)
    docs = loader.load()
    
    # 1. Fragmentación (Chunking) - Crucial para el análisis funcional
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    
    if docs:
        fragmentos = text_splitter.split_documents(docs)
        # 2. Embeddings y Base de Datos Vectorial
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=api_key)
        vectorstore = FAISS.from_documents(fragmentos, embeddings)
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    else:
        retriever = None

    # 3. Configuración de Gemini 1.5 Flash
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key, temperature=0.3)

    # Prompt Maestro en Alemán para comportamiento híbrido
    template = """
    Du bist ein hochspezialisierter KI-Experte für das Werk von J.R.R. Tolkien.
    Deine Aufgabe ist es, Fragen präzise und AUSSCHLIESSLICH AUF DEUTSCH zu beantworten.
    
    KONTEXT AUS DOKUMENTEN: {context}
    BENUTZERFRAGE: {question}
    
    REGELN:
    1. Antworte IMMER auf DEUTSCH.
    2. Nutze primär den KONTEXT y nenne die Datei.
    3. Falls die Info nicht im Kontext steht, nutze dein allgemeines Wissen auf Deutsch.
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
        return llm

agente = inicializar_motor()

# --- INTERFAZ DE CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("Ihre Frage an den Gelehrten..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Suche in den Archiven..."):
            if isinstance(agente, RetrievalQA):
                res = agente({"query": prompt})
                respuesta = res["result"]
                fuentes = res["source_documents"]
            else:
                # Fallback solo IA
                respuesta = agente.invoke(f"Antworte auf Deutsch: {prompt}").content
                fuentes = []

            st.markdown(respuesta)
            if fuentes:
                with st.expander("Quellen"):
                    for doc in fuentes:
                        st.caption(f"Datei: {doc.metadata.get('source')}")
            
            st.session_state.messages.append({"role": "assistant", "content": respuesta})
