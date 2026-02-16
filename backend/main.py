import os
import json
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings

# --- IMPORTACIÓN DEL AGENTE WEB MEJORADO ---
# Asegúrate de que backend/web_agent.py tenga la función 'search_and_structure'
try:
    from backend.web_agent import search_and_structure
except ImportError:
    print("⚠️ ADVERTENCIA: No se encontró 'backend.web_agent'. El scraping fallará.")
    def search_and_structure(name): return {"error": "Module missing", "raw_context": ""}

# 1. Configuración Inicial
load_dotenv()
app = FastAPI(title="HPE Sales Guardian API", version="4.0 (Structured Intelligence)")

# Configuración de CORS (Permite que el Frontend React hable con este Backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Clientes de IA y Base de Datos
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = "hpe_knowledge_base"

print("🧠 Cargando modelo de vectores (FastEmbed)...")
embeddings_model = FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")

# --- PROMPTS DE ROLES (PSICOLOGÍA DE VENTA) ---
ROLE_PROMPTS = {
    "CEO": "Enfócate en ROI, crecimiento de mercado, innovación y reducción de costos operativos (TCO). Sé visionario.",
    "CTO": "Enfócate en deuda técnica, escalabilidad, ciberseguridad, Kubernetes y modernización de infraestructura. Sé técnico.",
    "Vendedor": "Enfócate en ventajas competitivas rápidas, comparativas de precio y cierre de tratos (Time-to-value).",
    "SysAdmin": "Enfócate en facilidad de gestión, automatización (Ansible/Terraform) y reducción de tickets de soporte."
}

# Modelo de datos que recibimos del Frontend
class AnalyzeRequest(BaseModel):
    company_name: str
    url: str = "http://ignore.me" # Campo legado
    target_role: str = "CEO"

@app.get("/")
def read_root():
    return {"status": "System Online", "version": "4.0"}

@app.post("/analyze")
def analyze_company(request: AnalyzeRequest):
    print(f"\n🚀 INICIANDO ANÁLISIS: {request.company_name} | ROL: {request.target_role}")

    try:
        sources_used = []

        # --- PASO 1: INVESTIGACIÓN WEB ESTRUCTURADA (EL AGENTE) ---
        print("🌐 1. Ejecutando Agente de Investigación Web...")
        web_data = search_and_structure(request.company_name)
        
        # Extraemos el contexto texto para la IA y los datos visuales para el Frontend
        web_context_text = web_data.get("raw_context", "")
        if web_context_text:
            sources_used.append("Investigación Web en Vivo")
        else:
            sources_used.append("Web (Sin resultados)")

        # --- PASO 2: BÚSQUEDA EN MEMORIA INTERNA (QDRANT) ---
        print("📚 2. Consultando Base de Datos Vectorial (PDFs)...")
        internal_context_text = ""
        
        try:
            query_vector = embeddings_model.embed_query(f"HPE strategy for {request.company_name}")
            
            if QDRANT_URL and QDRANT_KEY:
                base_url = QDRANT_URL.rstrip('/')
                res = requests.post(
                    f"{base_url}/collections/{COLLECTION_NAME}/points/search",
                    headers={"api-key": QDRANT_KEY, "Content-Type": "application/json"},
                    json={"vector": query_vector, "limit": 3, "with_payload": True},
                    timeout=5
                )
                
                if res.status_code == 200:
                    results = res.json().get("result", [])
                    for item in results:
                        internal_context_text += f"- {item.get('payload', {}).get('text', '')}\n"
                    
                    if results:
                        sources_used.append("Base de Conocimiento Interna (HPE)")
                        print(f"   -> Encontrados {len(results)} fragmentos internos.")
                else:
                    print(f"   ⚠️ Error Qdrant: {res.status_code}")
        except Exception as q_err:
            print(f"   ⚠️ Falló Qdrant (continuando sin él): {q_err}")

        # --- PASO 3: SÍNTESIS DE ESTRATEGIA (RAG CON LLAMA 3) ---
        print("🤖 3. Generando Estrategia con IA...")
        
        role_instruction = ROLE_PROMPTS.get(request.target_role, ROLE_PROMPTS["CEO"])
        
        # Le pasamos a la IA los Triggers detectados específicamente
        triggers_detected = json.dumps(web_data.get("triggers", []))
        tech_stack_detected = json.dumps(web_data.get("tech_stack", []))

        system_prompt = f"""
        Eres 'HPE Sales Guardian', un asistente estratégico de ventas.
        
        OBJETIVO: Crear una estrategia de venta para {request.company_name} dirigida a un {request.target_role}.
        
        DIRECTRIZ DE ROL ({request.target_role}): {role_instruction}
        
        DATOS DE INTELIGENCIA DETECTADOS:
        - Triggers/Eventos: {triggers_detected}
        - Tecnología actual: {tech_stack_detected}
        
        INSTRUCCIONES:
        1. Analiza los Triggers. Si hay una "Expansión", vende GreenLake. Si hay "Ciberseguridad", vende Aruba.
        2. Usa el contexto interno (PDF) para alinear productos HPE.
        3. Si detectaste competidores (Cisco, Dell) en el stack, menciona sutilmente por qué HPE es mejor.
        
        FORMATO JSON RESPUESTA:
        {{
            "resumen_ejecutivo": "Visión general de la oportunidad...",
            "pain_points": ["Punto dolor 1", "Punto dolor 2"],
            "solucion_hpe_recomendada": "Nombre del Producto/Solución Clave",
            "speech_ventas": "El guion persuasivo para el correo o llamada..."
        }}
        """

        user_prompt = f"""
        Contexto Web Reciente: {web_context_text}
        Contexto Interno HPE: {internal_context_text}
        """

        completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.5,
            response_format={"type": "json_object"}
        )
        
        # Procesamos la respuesta de la IA
        ai_response_content = completion.choices[0].message.content
        
        # Validamos que sea JSON
        try:
            ai_json = json.loads(ai_response_content)
        except:
            # Fallback simple si la IA falla el formato
            ai_json = {
                "resumen_ejecutivo": "Análisis completado (formato texto plano).",
                "pain_points": ["Revisar manual"],
                "solucion_hpe_recomendada": "HPE GreenLake",
                "speech_ventas": ai_response_content
            }

        # --- PASO 4: RESPUESTA FINAL AL FRONTEND ---
        return {
            "company": request.company_name,
            # 1. La estrategia textual (Speech, Resumen)
            "analysis_json": json.dumps(ai_json), 
            # 2. Los datos visuales para los gráficos (Triggers, Stack, Score)
            "web_data": web_data, 
            # 3. Metadatos
            "sources": list(set(sources_used))
        }

    except Exception as e:
        print(f"🔥 ERROR CRÍTICO: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Bloque para correr localmente si se ejecuta el archivo directo
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)