import os
import json
from duckduckgo_search import DDGS
from groq import Groq
from dotenv import load_dotenv  # <--- 1. IMPORTANTE

# <--- 2. CARGAMOS LAS LLAVES AQUÍ MISMO
load_dotenv() 

# Cliente Groq independiente para el agente
# Ahora sí funcionará porque load_dotenv() ya corrió
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def search_and_structure(company_name: str):
    """
    1. Busca noticias recientes y datos técnicos en DuckDuckGo.
    2. Usa Llama 3 para 'leer' esos resultados y convertirlos en JSON estructurado.
    3. Retorna un diccionario con Triggers, Stack Tecnológico y Score sugerido.
    """
    print(f"🕵️‍♂️ AGENTE: Investigando a fondo a '{company_name}'...")
    
    try:
        # --- FASE 1: BÚSQUEDA ---
        query = f"{company_name} business news technology stack problems strategy 2024 2025"
        
        # Usamos DuckDuckGo
        results = DDGS().text(query, max_results=6)
        
        if not results:
            return {"error": "No information found"}

        raw_text = "\n".join([f"- {r['title']}: {r['body']}" for r in results])
        
        # --- FASE 2: PROCESAMIENTO CON LLAMA 3 ---
        system_prompt = """
        Eres un Analista de Inteligencia de Ventas B2B. Tu trabajo es extraer datos estructurados de noticias desordenadas.
        
        Analiza el texto y extrae el siguiente JSON estricto:
        {
            "industry": "Industria principal",
            "tech_stack": ["Lista", "de", "tecnologías", "mencionadas", "ej: AWS, SAP, Azure"],
            "competitors": ["Lista", "de", "competidores", "mencionados"],
            "triggers": [
                {
                    "type": "EXPANSION/LEADERSHIP/FINANCIAL/TECNOLOGIA",
                    "description": "Resumen breve del evento",
                    "sentiment": "POSITIVE/NEGATIVE"
                }
            ],
            "fit_score_reasoning": "Breve razón de por qué es un buen cliente o no"
        }
        
        REGLAS:
        - Si no encuentras info específica, deja la lista vacía [].
        - Prioriza noticias de 2024 y 2025.
        """

        completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Empresa: {company_name}\n\nNoticias Encontradas:\n{raw_text}"}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            response_format={"type": "json_object"}
        )

        structured_data = json.loads(completion.choices[0].message.content)
        structured_data["raw_context"] = raw_text
        
        print("✅ AGENTE: Datos estructurados con éxito.")
        return structured_data

    except Exception as e:
        print(f"🔥 AGENTE FALLÓ: {e}")
        return {"error": str(e), "raw_context": ""}