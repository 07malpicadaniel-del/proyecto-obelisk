import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
import requests

# Cargar entorno
load_dotenv()
qdrant_url = os.getenv("QDRANT_URL")
qdrant_key = os.getenv("QDRANT_API_KEY")

print(f"🔎 Analizando URL: {qdrant_url[:20]}...")

# --- INTENTO 1: Conexión HTTP Estándar (Requests) ---
# Esto verifica si es un problema de la librería qdrant_client o de tu internet
print("\n1️⃣  Probando conexión 'cruda' (Requests)...")
try:
    # Qdrant siempre tiene un endpoint /collections público si tienes la llave
    headers = {"api-key": qdrant_key}
    # Aseguramos que no tenga slash al final y agregamos el puerto si falta
    clean_url = qdrant_url.rstrip("/")
    r = requests.get(f"{clean_url}/collections", headers=headers, timeout=10)
    
    if r.status_code == 200:
        print(f"✅ ÉXITO (Requests): Tu internet SÍ llega a Qdrant. Respuesta: {r.json()}")
    else:
        print(f"⚠️ ALERTA: Llegamos, pero Qdrant rechazó con código {r.status_code}. Revisa tu API KEY.")
except Exception as e:
    print(f"🔥 FALLO TOTAL DE RED: {e}")
    print("   -> Posible causa: Firewall corporativo/escolar bloqueando la salida.")

# --- INTENTO 2: Cliente Oficial (Forzando Puerto 443) ---
print("\n2️⃣  Probando Cliente Oficial (Configuración Segura)...")
try:
    client = QdrantClient(
        url=qdrant_url,
        api_key=qdrant_key,
        port=443,  # Forzamos puerto HTTPS estándar
        https=True,
        timeout=20 # Damos más tiempo
    )
    cols = client.get_collections()
    print(f"🎉 ÉXITO (Cliente): Conexión estable. Colecciones: {cols}")
except Exception as e:
    print(f"❌ FALLO Cliente: {e}")

print("\n---------------------------------------")