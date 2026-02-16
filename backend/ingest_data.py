import os
from langchain_community.document_loaders import PyPDFLoader, TextLoader
# CORRECCIÓN 1: Importar desde el nuevo paquete específico
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
# CORRECCIÓN 2: Usar el conector oficial moderno
from langchain_qdrant import QdrantVectorStore
from dotenv import load_dotenv

load_dotenv()

# Configuración
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = "hpe_knowledge_base"
DATA_PATH = "data/" 

def ingest_docs():
    print("📂 Escaneando documentos en la carpeta 'data/'...")
    
    documents = []
    
    # 1. Cargar Archivos (PDF y TXT)
    if not os.path.exists(DATA_PATH):
        os.makedirs(DATA_PATH)
        print(f"⚠️ La carpeta {DATA_PATH} no existía, se ha creado. Coloca tus archivos ahí.")
        return

    for file in os.listdir(DATA_PATH):
        file_path = os.path.join(DATA_PATH, file)
        if file.endswith(".pdf"):
            print(f"   - Cargando PDF: {file}")
            loader = PyPDFLoader(file_path)
            documents.extend(loader.load())
        elif file.endswith(".txt"):
            print(f"   - Cargando TXT: {file}")
            loader = TextLoader(file_path, encoding="utf-8")
            documents.extend(loader.load())

    if not documents:
        print("❌ No hay documentos para procesar en 'data/'. Agrega el archivo hpe_knowledge.txt.")
        return

    # 2. Dividir en fragmentos (Chunks)
    print("🔪 Dividiendo texto en fragmentos digeribles...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100
    )
    docs = text_splitter.split_documents(documents)
    print(f"   -> Se generaron {len(docs)} fragmentos de conocimiento.")

    # 3. Vectorizar y Guardar en Qdrant
    print("🧠 Vectorizando e insertando en Qdrant (esto puede tardar)...")
    embeddings = FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")
    
    try:
        # CORRECCIÓN 3: Usamos QdrantVectorStore en lugar de Qdrant a secas
        QdrantVectorStore.from_documents(
            documents=docs,
            embedding=embeddings,
            url=QDRANT_URL,
            api_key=QDRANT_KEY,
            collection_name=COLLECTION_NAME,
            force_recreate=True 
        )
        print("✅ ¡ÉXITO! Base de conocimiento actualizada.")
        print("   Ahora tu IA sabe lo que dicen tus PDFs.")
        
    except Exception as e:
        print(f"🔥 Error al conectar con Qdrant: {e}")

if __name__ == "__main__":
    ingest_docs()