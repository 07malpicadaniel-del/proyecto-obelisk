# 🛡️ HPE Sales Guardian — Obelisk v6.0

Plataforma de Account Intelligence que detecta oportunidades de venta para HPE analizando información pública de empresas.

## Arquitectura

```
Frontend (React + Vite + Tailwind)
    ↓ HTTP
Backend (FastAPI + Python)
    ├── Web Agent (SerpAPI → DuckDuckGo fallback)
    ├── Product Matcher (trigger → producto HPE)
    ├── LLM (Groq Llama 3.3-70b)
    ├── SQLite (historial + Top 5)
    └── Qdrant (opcional — RAG con docs HPE)
```

## Setup Rápido (15 minutos)

### 1. Backend

```bash
cd proyecto-obelisk
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env         # Editar con tu GROQ_API_KEY
cd backend
python main.py                 # → http://localhost:8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev                    # → http://localhost:5173
```

## API Endpoints

| Método | Ruta       | Descripción                          |
|--------|-----------|--------------------------------------|
| GET    | /         | Health check                         |
| POST   | /analyze  | Analizar empresa (body: company_name, target_role) |
| GET    | /top5     | Top 5 empresas por oportunidad       |
| GET    | /history  | Historial de análisis                |

## Flujo del Sistema

1. Usuario ingresa nombre de empresa → frontend llama `/analyze`
2. Web Agent busca noticias (SerpAPI/DuckDuckGo) → Llama 3 estructura en JSON
3. Product Matcher mapea triggers detectados → producto HPE específico
4. LLM genera speech de 4 componentes (apertura, reto, vínculo, solución)
5. Resultado se guarda en SQLite → disponible en `/top5` y `/history`

## Tecnologías (todas gratuitas)

- **Groq** — Llama 3.3-70b (14,400 req/día gratis)
- **SerpAPI** — Google Search (100/mes gratis) + DuckDuckGo fallback ilimitado
- **SQLite** — Persistencia local, cero config
- **React + Vite + Tailwind** — Frontend moderno
- **FastAPI** — Backend Python
