import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from config.settings import OPENAI_API_KEY

DOCS_DIR = "documentos"
FAISS_PATH = "faiss_index"

def create_vector_store():
    archivos_txt = []
    for root, _, files in os.walk(DOCS_DIR):
        for f in files:
            if f.endswith(".txt"):
                archivos_txt.append(os.path.join(root, f))

    if not archivos_txt:
        return None

    documentos = []
    for ruta in archivos_txt:
        try:
            loader = TextLoader(ruta, encoding="utf-8")
            documentos.extend(loader.load())
        except Exception as e:
            print(f"Saltando {ruta}: {e}")

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = splitter.split_documents(documentos)
    print(f"Indexando {len(chunks)} fragmentos en FAISS...")

    embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
    vector_store = FAISS.from_documents(chunks, embeddings)
    vector_store.save_local(FAISS_PATH)
    print("¡Índice FAISS guardado correctamente!")
    return vector_store

def get_vector_store():
    embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
    if not os.path.exists(FAISS_PATH):
        return create_vector_store()
    return FAISS.load_local(FAISS_PATH, embeddings, allow_dangerous_deserialization=True)