import streamlit as st
from PyPDF2 import PdfReader
from langchain_openai import AzureOpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.chat_models import AzureChatOpenAI
from langchain.memory import ConversationBufferMemory
import os

embedding_args = {
    "azure_endpoint": "https://dhawalsingh-textembedding-3-small-dev-apimgmt.azure-api.net/",
    "api_version": "2024-03-01-preview",
    "deployment": "dhawalsingh-TextEmbedding-3-Small-Dev",
    "model": "text-embedding-3-small",
    "chunk_size": 1,
    "api_key": "f9e14857386d4041b8f0c6e9e21e221d"
}
embeddings = AzureOpenAIEmbeddings(**embedding_args)

st.set_page_config(page_title="Conversational PDF Chat", layout="wide")

with st.sidebar:
    st.title("PDF Chatbot")
    uploaded_files = st.file_uploader("Upload PDF files", type="pdf", accept_multiple_files=True)
    if st.button("Clear Conversation"):
        st.session_state.conversation_history = []
        st.session_state.memory.clear()

st.title("Conversational RAG Agent")

if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

if 'document_search' not in st.session_state:
    st.session_state.document_search = None

if 'memory' not in st.session_state:
    st.session_state.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

def save_faiss_index(faiss_index, file_path):
    faiss_index.save_local(file_path)

if uploaded_files:
    raw_text = ''
    for uploaded_file in uploaded_files:
        pdfreader = PdfReader(uploaded_file)
        for page in pdfreader.pages:
            content = page.extract_text()
            if content:
                raw_text += content

    text_splitter = CharacterTextSplitter(separator="\n", chunk_size=800, chunk_overlap=200, length_function=len)
    texts = text_splitter.split_text(raw_text)
    st.session_state.document_search = FAISS.from_texts(texts, embeddings)
    save_faiss_index(st.session_state.document_search, "faiss_index")

azure_chat = AzureChatOpenAI(
    openai_api_type="azure",
    azure_endpoint="https://dhawalsingh-gpt4-o-gs-dev-apimgmt.azure-api.net/",
    deployment_name="dhawalsingh-GPT4-O-GS-Dev",
    temperature=0,
    openai_api_key="4fbc8dc045fd4f36961a9f6557e0b56e",
    openai_api_version="2023-05-15"
)

if st.session_state.document_search:
    qa_chain = ConversationalRetrievalChain.from_llm(
        azure_chat,
        st.session_state.document_search.as_retriever(),
        memory=st.session_state.memory
    )

query = st.chat_input("Send a message:")
if query:
    if st.session_state.document_search:
        result = qa_chain({"question": query})
        answer = result['answer']
        st.session_state.conversation_history.append(("You", query))
        st.session_state.conversation_history.append(("Bot", answer))

for speaker, text in st.session_state.conversation_history:
    if speaker == "You":
        with st.chat_message("user"):
            st.write(text)
    elif speaker == "Bot":
        with st.chat_message("assistant"):
            st.write(text)