import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import warnings
import json
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from PyPDF2 import PdfReader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import ConversationalRetrievalChain
from langchain_openai import ChatOpenAI

# Configuración básica para el logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Suprime warnings innecesarias (opcional)
warnings.filterwarnings("ignore")

# --------------------------------------------------------------------------
# Configuración
# --------------------------------------------------------------------------
openai_api_key = "lm-studio"
# openai_base_url = "http://localhost:1234/v1"
openai_base_url = "http://host.docker.internal:1234/v1"

# Estas rutas se deben ajustar según como se monte la carpeta de datos en Docker.
knowledge_base_path = '/data/futuroterra_training'
chroma_db_dir = '/data/chroma_db'

# --------------------------------------------------------------------------
# Inicialización del modelo y de los embeddings
# --------------------------------------------------------------------------
llm = ChatOpenAI(
    temperature=0,
    openai_api_key=openai_api_key,
    openai_api_base=openai_base_url
)

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
collection_name = "futuroterra_collection"
vector_store = Chroma(
    embedding_function=embeddings,
    persist_directory=chroma_db_dir,
    collection_name=collection_name
)

# --------------------------------------------------------------------------
# Funciones auxiliares para carga y procesamiento de documentos
# --------------------------------------------------------------------------
def load_documents_from_folder(folder_path):
    documents = []
    filenames = []
    if not os.path.exists(folder_path):
        logging.warning("La carpeta no existe: %s", folder_path)
        return documents, filenames
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if filename.endswith(".md") or filename.endswith(".txt"):
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    documents.append(file.read())
                    filenames.append(filename)
            except Exception as e:
                logging.error("Error al leer %s: %s", filename, e)
        elif filename.endswith(".json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    json_content = json.load(file)
                    text = extract_text_from_json(json_content)
                    documents.append(text)
                    filenames.append(filename)
            except Exception as e:
                logging.error("Error al leer %s: %s", filename, e)
        elif filename.endswith(".pdf"):
            try:
                with open(file_path, 'rb') as file:
                    reader = PdfReader(file)
                    text = "".join(page.extract_text() for page in reader.pages)
                    documents.append(text)
                    filenames.append(filename)
            except Exception as e:
                logging.error("Error al leer %s: %s", filename, e)
    return documents, filenames

def extract_text_from_json(json_obj):
    texts = []
    if isinstance(json_obj, dict):
        for value in json_obj.values():
            texts.append(extract_text_from_json(value))
    elif isinstance(json_obj, list):
        for item in json_obj:
            texts.append(extract_text_from_json(item))
    elif isinstance(json_obj, str):
        texts.append(json_obj)
    return "\n".join(texts)

def split_texts_with_source(texts, sources):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = []
    chunk_sources = []
    for text, source in zip(texts, sources):
        split_chunks = text_splitter.split_text(text)
        chunks.extend(split_chunks)
        chunk_sources.extend([source] * len(split_chunks))
    return chunks, chunk_sources

# --------------------------------------------------------------------------
# Cargar documentos, dividir textos y actualizar el vector_store
# --------------------------------------------------------------------------
documents, filenames = load_documents_from_folder(knowledge_base_path)
chunks, chunk_sources = split_texts_with_source(documents, filenames)
existing_metadata = vector_store.get()["metadatas"]
existing_filenames = set(meta.get("source") for meta in existing_metadata if "source" in meta)

new_texts = []
new_metadata = []
for text, source in zip(chunks, chunk_sources):
    if source not in existing_filenames:
        new_texts.append(text)
        new_metadata.append({"source": source})

if new_texts:
    vector_store.add_texts(texts=new_texts, metadatas=new_metadata)
    logging.info("✅ Se han cargado %d nuevos embeddings a ChromaDB.", len(new_texts))
else:
    logging.info("ℹ️ No se han encontrado nuevos embeddings para cargar a ChromaDB.")

# --------------------------------------------------------------------------
# Función de chatbot (RAG: Retrieval-Augmented Generation)
# --------------------------------------------------------------------------
def rag(query, chat_history):
    retriever = vector_store.as_retriever()
    qa_chain = ConversationalRetrievalChain.from_llm(llm=llm, retriever=retriever)
    result = qa_chain.invoke({"question": query, "chat_history": chat_history})
    return result['answer']

# --------------------------------------------------------------------------
# Configuración de la aplicación Flask
# --------------------------------------------------------------------------
app = Flask(__name__)
CORS(app)

# Se utiliza una variable en memoria para almacenar el historial de chat
chat_history = []

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    query = data.get("message", "")
    logging.info("Mensaje recibido desde el frontend: %s", query)
    
    if not query:
        return jsonify({"error": "No se ha proporcionado un mensaje."}), 400

    try:
        response = rag(query, chat_history)
        chat_history.append((query, response))
        logging.info("Respuesta enviada: %s", response)
        return jsonify({"response": response})
    except Exception as e:
        logging.error("Error al procesar el mensaje: %s", e)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # La app escucha en todas las interfaces para que Docker pueda acceder a ella
    app.run(host='0.0.0.0', port=8000)
