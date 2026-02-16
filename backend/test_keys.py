import os
from dotenv import load_dotenv
from groq import Groq
from qdrant_client import QdrantClient

# 1. Cargar las llaves del archivo .env
print("🔌 Cargando variables de entorno...")
load_dotenv() # Esto busca el archivo .env automáticamente

groq_key = os.getenv("GROQ_API_KEY")
qdrant_url = os.getenv("QDRANT_URL")
qdrant_key = os.getenv("QDRANT_API_KEY")

# Verificación visual (solo imprimimos los primeros caracteres por seguridad)
if groq_key:
    print(f"✅ Groq Key detectada: {groq_key[:4]}...OK")
else:
    print("❌ ERROR: No se encontró GROQ_API_KEY")

if qdrant_url and qdrant_key:
    print(f"✅ Qdrant Config detectada: URL termina en ...{qdrant_url[-10:]}")
else:
    print("❌ ERROR: Faltan credenciales de Qdrant")

print("\n--- INICIANDO PRUEBA DE CONEXIÓN ---\n")

# 2. Prueba de DeepSeek (Groq)
try:
    print("🧠 Intentando conectar con DeepSeek-R1 en Groq...")
    groq_client = Groq(api_key=groq_key)
    chat_completion = groq_client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "Responde solo con la palabra: 'CONECTADO'",
            }
        ],
        model="llama-3.3-70b-versatile",
    )
    print(f"🎉 ÉXITO GROQ: La IA respondió -> {chat_completion.choices[0].message.content}")
except Exception as e:
    print(f"🔥 FALLO GROQ: {e}")

# 3. Prueba de Memoria (Qdrant)
try:
    print("\n📚 Intentando conectar con Qdrant Cloud...")
    qdrant_client = QdrantClient(
        url=qdrant_url,
        api_key=qdrant_key,
    )
    # Intentamos listar las colecciones (debería estar vacío, pero no dar error)
    collections = qdrant_client.get_collections()
    print(f"🎉 ÉXITO QDRANT: Conexión establecida. Colecciones encontradas: {collections}")
except Exception as e:
    print(f"🔥 FALLO QDRANT: {e}")

print("\n---------------------------------------")