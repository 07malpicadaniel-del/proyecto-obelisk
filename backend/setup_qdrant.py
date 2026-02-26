import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models

# 1. Cargar credenciales
load_dotenv()
qdrant_url = os.getenv("QDRANT_URL")
qdrant_key = os.getenv("QDRANT_API_KEY")

# Nombre de tu "Cerebro" (Colección)
COLLECTION_NAME = "hpe_knowledge_base"

def create_collection():
    print("⏳ Conectando a Qdrant...")
    
    # Usamos la configuración segura que nos funcionó (Puerto 443)
    client = QdrantClient(
        url=qdrant_url,
        api_key=qdrant_key,
        port=443,
        https=True,
        timeout=20
    )

    # 2. Verificar si ya existe
    if client.collection_exists(collection_name=COLLECTION_NAME):
        print(f"✅ La colección '{COLLECTION_NAME}' ya existe. No es necesario hacer nada.")
        return

    # 3. Crear la colección si no existe
    print(f"🔨 Creando colección '{COLLECTION_NAME}'...")
    
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(
            size=384,  # TAMAÑO CRÍTICO: Debe coincidir con el modelo de Embeddings (FastEmbed)
            distance=models.Distance.COSINE  # La matemática para medir "similitud"
        )
    )
    
    print(f"🎉 ¡ÉXITO! Colección '{COLLECTION_NAME}' creada y lista para recibir vectores.")

if __name__ == "__main__":
    try:
        create_collection()
    except Exception as e:
        print(f"🔥 Error fatal: {e}")