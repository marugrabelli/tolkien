import streamlit as st
import os
import google.generativeai as genai

# Importaciones protegidas
try:
    from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
    from langchain_community.vectorstores import FAISS
    from langchain.chains import RetrievalQA
    from langchain.prompts import PromptTemplate
except ImportError:
    st.error("⚠️ Error: LangChain no está instalado. Verifica que 'requirements.txt' esté en la raíz de tu GitHub.")
    st.stop()

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Tolkien Hybrid Agent", page_icon="🧙‍♂️")
st.title("🧙‍♂️ Tolkiendil Hybrid-Assistent")

if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
else:
    st.error("⚠️ Falta GOOGLE_API_KEY en Secrets.")
    st.stop()

# --- MOTOR RAG HÍBRIDO ---
@st.cache_resource
def setup_engine():
    path = "./conocimiento/"
    if not os.path.exists(path):
        os.makedirs(path)
    
    loader = DirectoryLoader(path, glob="./*.pdf", loader_cls=PyPDFLoader)
    docs = loader.load()
    
    # Fragmentación (Chunking) para análisis semántico
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    
    if docs:
        fragmentos = text_splitter.split_documents(docs)
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=api_key)
        vectorstore = FAISS.from_documents(fragmentos, embeddings)
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    else:
        retriever = None

    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key, temperature=0.3)

    template = """
    Du bist ein Experte für J.R.R. Tolkien. Antworte IMMER auf DEUTSCH.
    KONTEXT: {context}
    FRAGE: {question}
    
    ANWEISUNGEN:
    1. Nutze den KONTEXT, falls vorhanden.
    2. Wenn nicht im Kontext, nutze dein Wissen auf Deutsch.
    3. Ende: '💡 Tolkien Fun Fact' (Deutsch).
    """
    
    QA_PROMPT = PromptTemplate(template=template, input_variables=["context", "question"])

    if retriever:
        return RetrievalQA.from_chain_type(
            llm=llm,
            retriever=retriever,
            chain_type_kwargs={"prompt": QA_PROMPT},
            return_source_documents=True
        )
    return llm

agente = setup_engine()

# --- CHAT ---
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
        if isinstance(agente, RetrievalQA):
            res = agente({"query": prompt})
            respuesta = res["result"]
            if res["source_documents"]:
                with st.expander("Quellen"):
                    for d in res["source_documents"]:
                        st.caption(f"Datei: {d.metadata.get('source')}")
        else:
            respuesta = agente.invoke(f"Antworte auf Deutsch: {prompt}").content
        
        st.markdown(respuesta)
        st.session_state.messages.append({"role": "assistant", "content": respuesta})
