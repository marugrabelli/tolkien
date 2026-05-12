import streamlit as st
import os
import google.generativeai as genai
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Tolkien Hybrid Agent", page_icon="🧙‍♂️")
st.title("🧙‍♂️ Tolkiendil Hybrid-Assistent")

if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
else:
    st.error("⚠️ Bitte GOOGLE_API_KEY in Streamlit Secrets konfigurieren.")
    st.stop()

# --- LOGICA DE PROCESAMIENTO (FRAGMENTACIÓN Y RAG) ---
@st.cache_resource
def setup_ai_engine():
    # 1. Carga de archivos
    path = "./conocimiento/"
    if not os.path.exists(path):
        os.makedirs(path)
    
    # Soporte para PDF y TXT
    loader = DirectoryLoader(path, glob="./*", loader_cls=PyPDFLoader)
    docs = loader.load()
    
    if not docs:
        return None

    # 2. Fragmentación Estratégica (Chunking)
    # Usamos 1000 caracteres con solapamiento para mantener la narrativa
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(docs)

    # 3. Embeddings y Base de Datos Vectorial
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=api_key)
    vectorstore = FAISS.from_documents(splits, embeddings)

    # 4. Configuración del Agente Híbrido
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key, temperature=0.3)

    # PROMPT MAESTRO EN ALEMÁN
    template = """
    Du bist ein spezialisierter KI-Experte für J.R.R. Tolkien.
    Deine Aufgabe ist es, Fragen präzise und ausschließlich auf DEUTSCH zu beantworten.
    
    KONTEXT AUS DOKUMENTEN: {context}
    FRAGE: {question}
    
    REGELN:
    1. Antworte IMMER auf DEUTSCH.
    2. Wenn die Antwort im KONTEXT steht, verwende sie und nenne die Quelle.
    3. Wenn die Information NICHT im Kontext steht, nutze dein allgemeines KI-Wissen, aber weise höflich darauf hin.
    4. Füge am Ende immer einen '💡 Tolkien Fun Fact' auf Deutsch hinzu.
    """
    
    QA_PROMPT = PromptTemplate(template=template, input_variables=["context", "question"])

    return RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
        chain_type_kwargs={"prompt": QA_PROMPT},
        return_source_documents=True
    )

agente = setup_ai_engine()

# --- INTERFAZ DE USUARIO ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("Schreiben Sie Ihre Frage..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Suche in der Bibliothek..."):
            if agente:
                res = agente({"query": prompt})
                response = res["result"]
                sources = res["source_documents"]
            else:
                # Fallback solo IA si no hay archivos
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(f"Antworte auf Deutsch: {prompt}").text
                sources = []

            st.markdown(response)
            if sources:
                with st.expander("Verwendete Quellen"):
                    for doc in sources:
                        st.caption(f"Datei: {doc.metadata.get('source')}")
            
            st.session_state.messages.append({"role": "assistant", "content": response})
