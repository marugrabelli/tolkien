import streamlit as st
import os
import google.generativeai as genai
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Tolkien Expert", page_icon="🧙‍♂️")
st.title("🧙‍♂️ Tolkiendil Assistent")

if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
else:
    st.error("⚠️ GOOGLE_API_KEY missing in Secrets.")
    st.stop()

# --- MOTOR RAG ---
@st.cache_resource
def setup_engine():
    path = "./conocimiento/"
    if not os.path.exists(path):
        os.makedirs(path)
    
    loader = DirectoryLoader(path, glob="./*.pdf", loader_cls=PyPDFLoader)
    docs = loader.load()
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    
    if docs:
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
        if hasattr(agente, "invoke"):
            # Si es RetrievalQA
            res = agente({"query": prompt})
            respuesta = res["result"]
        else:
            # Si es solo el LLM
            respuesta = agente.invoke(f"Antworte auf Deutsch: {prompt}").content
        
        st.markdown(respuesta)
        st.session_state.messages.append({"role": "assistant", "content": respuesta})
