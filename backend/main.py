"""
main.py — HPE Sales Guardian / Obelisk
FastAPI Backend v8.1 — Background Scanner, Alerts, 3 Recommendations
"""
import os, sys, json, sqlite3
from datetime import datetime
from pathlib import Path
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from groq import Groq
import threading
import time as _time

sys.path.append(os.path.dirname(__file__))
from web_agent import search_and_structure
from product_matcher import find_best_product, find_top3_products
from scanner import scan_all_accounts, scan_account
from scoring import calculate_score

load_dotenv()

app = FastAPI(title="HPE Sales Guardian", version="8.1")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = "hpe_knowledge_base"

embeddings_model = None
if QDRANT_URL and QDRANT_KEY:
    try:
        from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
        embeddings_model = FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")
    except: pass

# ── SQLite ────────────────────────────────────────────────────────────────────
DB_PATH = Path(__file__).parent.parent / "data" / "obelisk.db"

def get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    conn.execute("""CREATE TABLE IF NOT EXISTS analysis_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT, company_name TEXT NOT NULL,
        industry TEXT, fit_score INTEGER, triggers TEXT, tech_stack TEXT,
        competitors TEXT, hpe_product_recommended TEXT, hpe_product_category TEXT,
        speech TEXT, resumen TEXT, pain_points TEXT, target_role TEXT, sources TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT NOT NULL UNIQUE,
        contact_name TEXT DEFAULT '', contact_role TEXT DEFAULT '',
        industry TEXT DEFAULT '', website TEXT DEFAULT '',
        context TEXT DEFAULT '', notes TEXT DEFAULT '',
        last_score INTEGER DEFAULT 0, last_product TEXT DEFAULT '',
        last_status TEXT DEFAULT 'NEW',
        created_at TEXT DEFAULT (datetime('now')), updated_at TEXT DEFAULT (datetime('now'))
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT, account_id INTEGER,
        role TEXT NOT NULL, content TEXT NOT NULL,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (account_id) REFERENCES accounts(id)
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_id INTEGER, company_name TEXT NOT NULL,
        alert_level TEXT DEFAULT 'MEDIUM',
        summary TEXT, new_triggers TEXT, score_change INTEGER DEFAULT 0,
        fit_score INTEGER DEFAULT 0, recommended_product TEXT DEFAULT '',
        is_read INTEGER DEFAULT 0, dismissed INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (account_id) REFERENCES accounts(id)
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS scanner_config (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        enabled INTEGER DEFAULT 1,
        interval_hours REAL DEFAULT 6,
        last_scan_at TEXT,
        last_scan_results TEXT
    )""")
    conn.execute("INSERT OR IGNORE INTO scanner_config (id, enabled, interval_hours) VALUES (1, 1, 168)")
    conn.execute("UPDATE scanner_config SET interval_hours=168 WHERE id=1")
    for col, default in [("contact_name","''"),("contact_role","''"),("context","''")]:
        try: conn.execute(f"ALTER TABLE accounts ADD COLUMN {col} TEXT DEFAULT {default}")
        except: pass
    conn.commit(); conn.close()
    print("SQLite v8.1 ready (with alerts & scanner)")

init_db()

# ── Background Scanner Thread ─────────────────────────────────────────────────
scanner_thread = None
scanner_running = False

def _scanner_loop():
    global scanner_running
    print("[SCANNER] Background scanner started")
    while scanner_running:
        try:
            conn = get_conn()
            config = conn.execute("SELECT enabled, interval_hours, last_scan_at FROM scanner_config WHERE id=1").fetchone()
            conn.close()
            if not config or not config["enabled"]:
                _time.sleep(60); continue
            interval_secs = config["interval_hours"] * 3600
            last_scan = config["last_scan_at"]
            should_scan = True
            if last_scan:
                try:
                    last_dt = datetime.fromisoformat(last_scan)
                    elapsed = (datetime.utcnow() - last_dt).total_seconds()
                    should_scan = elapsed >= interval_secs
                except: pass
            if should_scan:
                print(f"[SCANNER] Triggering scheduled scan...")
                results = scan_all_accounts()
                conn = get_conn()
                conn.execute("UPDATE scanner_config SET last_scan_at=datetime('now'), last_scan_results=? WHERE id=1",
                    (json.dumps({"scanned": len(results), "alerts": sum(1 for r in results if r.get('alert_level','NONE') != 'NONE')}, ensure_ascii=False),))
                conn.commit(); conn.close()
            _time.sleep(60)  # Check every minute
        except Exception as e:
            print(f"[SCANNER] Error in loop: {e}")
            _time.sleep(120)

def start_scanner():
    global scanner_thread, scanner_running
    if scanner_thread and scanner_thread.is_alive(): return
    scanner_running = True
    scanner_thread = threading.Thread(target=_scanner_loop, daemon=True)
    scanner_thread.start()

@app.on_event("startup")
async def startup_event():
    start_scanner()

def save_analysis(data: dict):
    try:
        conn = get_conn()
        conn.execute("""INSERT INTO analysis_history 
            (company_name,industry,fit_score,triggers,tech_stack,competitors,
             hpe_product_recommended,hpe_product_category,speech,resumen,pain_points,target_role,sources)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (data.get("company_name"), data.get("industry"), data.get("fit_score"),
             json.dumps(data.get("triggers",[]),ensure_ascii=False),
             json.dumps(data.get("tech_stack",[]),ensure_ascii=False),
             json.dumps(data.get("competitors",[]),ensure_ascii=False),
             data.get("hpe_product"), data.get("hpe_category"),
             data.get("speech"), data.get("resumen"),
             json.dumps(data.get("pain_points",[]),ensure_ascii=False),
             data.get("target_role"), json.dumps(data.get("sources",[]),ensure_ascii=False)))
        conn.execute("""UPDATE accounts SET last_score=?, last_product=?, last_status=?,
            industry=?, updated_at=datetime('now') WHERE LOWER(company_name)=LOWER(?)""",
            (data.get("fit_score"), data.get("hpe_product"), "ANALYZED", data.get("industry"), data.get("company_name")))
        conn.commit(); conn.close()
    except Exception as e: print(f"SQLite save error: {e}")

# ── Account endpoints ─────────────────────────────────────────────────────────
class AccountCreate(BaseModel):
    company_name: str = ""; contact_name: str = ""; contact_role: str = ""
    industry: str = ""; website: str = ""; context: str = ""; notes: str = ""

class AccountUpdate(BaseModel):
    contact_name: Optional[str] = None; contact_role: Optional[str] = None
    industry: Optional[str] = None; website: Optional[str] = None
    context: Optional[str] = None; notes: Optional[str] = None

@app.get("/accounts")
def list_accounts():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM accounts ORDER BY updated_at DESC").fetchall()
    conn.close()
    return {"accounts": [dict(r) for r in rows]}

@app.post("/accounts")
def create_account(req: AccountCreate):
    name = req.company_name.strip()
    if not name and not req.website.strip():
        raise HTTPException(400, "Company name or website is required")
    if not name:
        # Derive name from website
        name = req.website.strip().replace("https://","").replace("http://","").replace("www.","").split("/")[0].split(".")[0].capitalize()
    conn = get_conn()
    try:
        conn.execute("INSERT INTO accounts (company_name,contact_name,contact_role,industry,website,context,notes) VALUES (?,?,?,?,?,?,?)",
            (name, req.contact_name, req.contact_role, req.industry, req.website, req.context, req.notes))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close(); raise HTTPException(400, "Account already exists")
    row = conn.execute("SELECT * FROM accounts WHERE LOWER(company_name)=LOWER(?)", (name,)).fetchone()
    conn.close()
    return dict(row)

@app.patch("/accounts/{account_id}")
def update_account(account_id: int, req: AccountUpdate):
    conn = get_conn()
    acct = conn.execute("SELECT * FROM accounts WHERE id=?", (account_id,)).fetchone()
    if not acct: conn.close(); raise HTTPException(404, "Not found")
    updates = {k: v for k, v in req.dict().items() if v is not None}
    if updates:
        sets = ", ".join(f"{k}=?" for k in updates)
        conn.execute(f"UPDATE accounts SET {sets}, updated_at=datetime('now') WHERE id=?", list(updates.values())+[account_id])
        conn.commit()
    row = conn.execute("SELECT * FROM accounts WHERE id=?", (account_id,)).fetchone()
    conn.close()
    return dict(row)

@app.delete("/accounts/{account_id}")
def delete_account(account_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM accounts WHERE id=?", (account_id,))
    conn.execute("DELETE FROM chat_messages WHERE account_id=?", (account_id,))
    conn.commit(); conn.close()
    return {"ok": True}

@app.get("/accounts/{account_id}/history")
def account_history(account_id: int):
    conn = get_conn()
    acct = conn.execute("SELECT company_name FROM accounts WHERE id=?", (account_id,)).fetchone()
    if not acct: conn.close(); raise HTTPException(404, "Not found")
    rows = conn.execute("SELECT * FROM analysis_history WHERE LOWER(company_name)=LOWER(?) ORDER BY created_at DESC LIMIT 10", (acct["company_name"],)).fetchall()
    conn.close()
    return {"history": [dict(r) for r in rows]}

# ── Chat ──────────────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str; account_id: Optional[int] = None; company_context: str = ""

@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    account_context = ""
    if req.account_id:
        conn = get_conn()
        acct = conn.execute("SELECT * FROM accounts WHERE id=?", (req.account_id,)).fetchone()
        if acct:
            account_context = f"Account: {acct['company_name']} | Industry: {acct['industry']}"
            if acct['contact_name']: account_context += f"\nContact: {acct['contact_name']} ({acct['contact_role']})"
            if acct['context']: account_context += f"\nSales context: {acct['context']}"
            last = conn.execute("SELECT resumen,triggers,tech_stack,competitors,hpe_product_recommended,fit_score FROM analysis_history WHERE LOWER(company_name)=LOWER(?) ORDER BY created_at DESC LIMIT 1", (acct["company_name"],)).fetchone()
            if last:
                account_context += f"\nLast analysis: Score {last['fit_score']} | Product: {last['hpe_product_recommended']}"
                account_context += f"\nSummary: {last['resumen']}\nTriggers: {last['triggers']}\nCompetitors: {last['competitors']}"
        conn.execute("INSERT INTO chat_messages (account_id,role,content) VALUES (?,'user',?)", (req.account_id, req.message))
        conn.commit(); conn.close()
    if req.company_context: account_context += f"\nAdditional: {req.company_context}"

    needs_search = any(kw in req.message.lower() for kw in ["search","look up","find","research","news","latest","recent","what's happening","investigate","check","update"])
    search_results = ""
    if needs_search:
        try:
            from web_agent import _search_serpapi, _search_duckduckgo
            results = _search_serpapi(req.company_context or req.message) or _search_duckduckgo(req.company_context or req.message)
            if results: search_results = "\n\nWEB SEARCH:\n" + "\n".join([f"- [{r.get('date','')}] {r.get('title','')}: {r.get('body',r.get('snippet',''))}" for r in results[:8]])
        except: pass

    system = f"""You are HPE Sales Guardian AI assistant for HPE sales reps. English only.
HPE products: Compute (ProLiant, Synergy), Storage (Alletra, Primera), Networking (Aruba), Hybrid Cloud (GreenLake), AI/ML (Cray), Security (Zero Trust).
{f'ACCOUNT CONTEXT:{chr(10)}{account_context}' if account_context else ''}{search_results}
Keep answers focused and actionable."""

    try:
        completion = groq_client.chat.completions.create(
            messages=[{"role":"system","content":system},{"role":"user","content":req.message}],
            model="llama-3.3-70b-versatile", temperature=0.4)
        reply = completion.choices[0].message.content
        if req.account_id:
            conn = get_conn()
            conn.execute("INSERT INTO chat_messages (account_id,role,content) VALUES (?,'assistant',?)", (req.account_id, reply))
            conn.commit(); conn.close()
        return {"reply": reply, "searched": needs_search}
    except Exception as e: raise HTTPException(500, str(e))

@app.get("/chat/{account_id}/messages")
def get_chat_messages(account_id: int, limit: int = 50):
    conn = get_conn()
    rows = conn.execute("SELECT role,content,created_at FROM chat_messages WHERE account_id=? ORDER BY created_at ASC LIMIT ?", (account_id, limit)).fetchall()
    conn.close()
    return {"messages": [dict(r) for r in rows]}

# ── Top 5 & History ───────────────────────────────────────────────────────────
@app.get("/top5")
def top5_endpoint():
    conn = get_conn()
    rows = conn.execute("SELECT company_name,fit_score,hpe_product_recommended,industry,created_at FROM analysis_history ORDER BY fit_score DESC LIMIT 5").fetchall()
    conn.close()
    return {"top5": [dict(r) for r in rows]}

@app.get("/history")
def history_endpoint(limit: int = 20):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM analysis_history ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return {"history": [dict(r) for r in rows]}

# ── Alerts ───────────────────────────────────────────────────────────────────
@app.get("/alerts")
def get_alerts(limit: int = 50, unread_only: bool = False):
    conn = get_conn()
    q = "SELECT * FROM alerts WHERE dismissed=0"
    if unread_only: q += " AND is_read=0"
    q += " ORDER BY created_at DESC LIMIT ?"
    rows = conn.execute(q, (limit,)).fetchall()
    unread = conn.execute("SELECT COUNT(*) as c FROM alerts WHERE is_read=0 AND dismissed=0").fetchone()["c"]
    conn.close()
    return {"alerts": [dict(r) for r in rows], "unread_count": unread}

@app.post("/alerts/{alert_id}/read")
def mark_alert_read(alert_id: int):
    conn = get_conn()
    conn.execute("UPDATE alerts SET is_read=1 WHERE id=?", (alert_id,))
    conn.commit(); conn.close()
    return {"ok": True}

@app.post("/alerts/read-all")
def mark_all_read():
    conn = get_conn()
    conn.execute("UPDATE alerts SET is_read=1 WHERE is_read=0")
    conn.commit(); conn.close()
    return {"ok": True}

@app.post("/alerts/{alert_id}/dismiss")
def dismiss_alert(alert_id: int):
    conn = get_conn()
    conn.execute("UPDATE alerts SET dismissed=1 WHERE id=?", (alert_id,))
    conn.commit(); conn.close()
    return {"ok": True}

# ── Scanner Control ─────────────────────────────────────────────────────────────
@app.get("/scanner/status")
def scanner_status():
    conn = get_conn()
    config = conn.execute("SELECT * FROM scanner_config WHERE id=1").fetchone()
    acct_count = conn.execute("SELECT COUNT(*) as c FROM accounts").fetchone()["c"]
    conn.close()
    return {
        "enabled": bool(config["enabled"]) if config else False,
        "interval_hours": config["interval_hours"] if config else 6,
        "last_scan_at": config["last_scan_at"] if config else None,
        "last_scan_results": json.loads(config["last_scan_results"]) if config and config["last_scan_results"] else None,
        "accounts_monitored": acct_count,
        "thread_alive": scanner_thread.is_alive() if scanner_thread else False,
    }

class ScannerUpdate(BaseModel):
    enabled: Optional[bool] = None
    interval_hours: Optional[float] = None

@app.patch("/scanner/config")
def update_scanner_config(req: ScannerUpdate):
    conn = get_conn()
    if req.enabled is not None:
        conn.execute("UPDATE scanner_config SET enabled=? WHERE id=1", (1 if req.enabled else 0,))
    if req.interval_hours is not None:
        conn.execute("UPDATE scanner_config SET interval_hours=? WHERE id=1", (max(0.1, req.interval_hours),))
    conn.commit()
    config = conn.execute("SELECT * FROM scanner_config WHERE id=1").fetchone()
    conn.close()
    return dict(config)

@app.post("/scanner/run-now")
def run_scan_now():
    """Trigger an immediate scan of all accounts."""
    results = scan_all_accounts()
    conn = get_conn()
    conn.execute("UPDATE scanner_config SET last_scan_at=datetime('now'), last_scan_results=? WHERE id=1",
        (json.dumps({"scanned": len(results), "alerts": sum(1 for r in results if r.get('alert_level','NONE') != 'NONE')}, ensure_ascii=False),))
    conn.commit(); conn.close()
    return {"results": results, "scanned": len(results), "alerts_generated": sum(1 for r in results if r.get('alert_level','NONE') != 'NONE')}

@app.post("/scanner/scan-one/{account_id}")
def scan_one_account(account_id: int):
    conn = get_conn()
    acct = conn.execute("SELECT company_name FROM accounts WHERE id=?", (account_id,)).fetchone()
    conn.close()
    if not acct: raise HTTPException(404, "Account not found")
    result = scan_account(acct["company_name"])
    return result

@app.get("/")
def health(): return {"status": "online", "version": "8.1"}

# ── Analyze ───────────────────────────────────────────────────────────────────
ROLE_PROMPTS = {
    "CEO": "Focus on ROI, TCO reduction, market growth, competitive advantage. Executive language.",
    "CTO": "Focus on technical debt, scalability, Kubernetes, Zero Trust, modernization. Technical and precise.",
    "Vendedor": "Focus on time-to-value, competitive differentiation, fast close. Direct sales language.",
}

class AnalyzeRequest(BaseModel):
    company_name: str; target_role: str = "CEO"; url: str = ""
    account_context: str = ""; contact_name: str = ""

@app.post("/analyze")
def analyze_company(request: AnalyzeRequest):
    print(f"\n{'='*60}\nANALYSIS v8: {request.company_name} | ROLE: {request.target_role}\n{'='*60}")
    sources_used = []

    # Auto-create account
    conn = get_conn()
    existing = conn.execute("SELECT id,contact_name,contact_role,context FROM accounts WHERE LOWER(company_name)=LOWER(?)", (request.company_name,)).fetchone()
    if not existing:
        conn.execute("INSERT OR IGNORE INTO accounts (company_name) VALUES (?)", (request.company_name,))
        conn.commit()
        acct_contact = request.contact_name; acct_context = request.account_context
    else:
        acct_contact = existing["contact_name"] or request.contact_name
        acct_context = existing["context"] or request.account_context
    conn.close()

    # 1. Web Intelligence
    web_data = search_and_structure(request.company_name)
    web_context = web_data.get("raw_context", "")
    sources_used.append(web_data.get("_source", "Web") if web_context else "No web data")

    # 2. Top 3 Products
    triggers = web_data.get("triggers", [])
    tech_stack = web_data.get("tech_stack", [])
    industry = web_data.get("industry", "")
    top3 = find_top3_products(triggers, tech_stack, industry)
    primary = top3[0] if top3 else find_best_product(triggers, tech_stack, industry)

    # 3. Qdrant RAG
    internal_context = ""
    if embeddings_model and QDRANT_URL and QDRANT_KEY:
        try:
            vector = embeddings_model.embed_query(f"HPE {primary['producto_nombre']} for {request.company_name}")
            res = requests.post(f"{QDRANT_URL.rstrip('/')}/collections/{COLLECTION_NAME}/points/search",
                headers={"api-key": QDRANT_KEY, "Content-Type": "application/json"},
                json={"vector": vector, "limit": 3, "with_payload": True}, timeout=5)
            if res.status_code == 200:
                hits = res.json().get("result", [])
                internal_context = "\n".join(h.get("payload",{}).get("text","") for h in hits)
                if hits: sources_used.append("HPE Knowledge Base (Qdrant)")
        except: pass

    # 4. Validate
    is_competitor = web_data.get("is_hpe_competitor", False)
    has_signals = web_data.get("has_useful_signals", len(triggers) > 0)

    if is_competitor:
        return {"company": request.company_name, "analysis_json": json.dumps({
            "resumen_ejecutivo": f"{request.company_name} is a direct HPE competitor.",
            "pain_points":[],"solucion_hpe_recomendada":"N/A",
            "speech_opening":"","speech_challenge":"","speech_bridge":"","speech_solution":"",
            "speech_resumen":f"{request.company_name} competes with HPE.",
            "referencia_hpe":"","recommendation_status":"COMPETITOR"
        },ensure_ascii=False), "web_data":web_data, "top3_recommendations": [],
            "fit_score":0,"sources":list(set(sources_used)),"has_opportunity":False,"is_competitor":True}

    if not has_signals:
        fit_score = max(5, len(tech_stack)*2)
        return {"company":request.company_name,"analysis_json":json.dumps({
            "resumen_ejecutivo":f"No IT signals detected for {request.company_name}.",
            "pain_points":[],"solucion_hpe_recomendada":"None",
            "speech_opening":"","speech_challenge":"","speech_bridge":"","speech_solution":"",
            "speech_resumen":f"No signals at {request.company_name}. Monitor periodically.",
            "referencia_hpe":"","recommendation_status":"NO_OPPORTUNITY"
        },ensure_ascii=False),"web_data":web_data,"top3_recommendations":[],
            "fit_score":fit_score,"sources":list(set(sources_used)),"has_opportunity":False,"is_competitor":False}

    # 5. AI — structured 4-part speech + internal brief
    role_instruction = ROLE_PROMPTS.get(request.target_role, ROLE_PROMPTS["CEO"])

    # Build recommendations context for prompt
    recs_text = ""
    for i, rec in enumerate(top3):
        recs_text += f"\nRECOMMENDATION {i+1}: {rec['producto_nombre']} ({rec['categoria']})\n"
        recs_text += f"  URL: {rec['url']}\n"
        recs_text += f"  Needs: {', '.join(rec['need_detected'])}\n"
        recs_text += f"  Relationship: {rec['relationship']}\n"
        recs_text += f"  Competitive edge: {rec['competitive_advantage']}\n"

    account_extra = ""
    if acct_contact: account_extra += f"\nCONTACT: {acct_contact}"
    if acct_context: account_extra += f"\nSALES CONTEXT: {acct_context}"

    system_prompt = f"""You are 'HPE Sales Guardian', expert B2B sales intelligence for HPE.

TARGET: {request.company_name} | ROLE: {request.target_role}
DIRECTIVE: {role_instruction}
{account_extra}

TOP 3 HPE RECOMMENDATIONS:
{recs_text}

TRIGGERS: {json.dumps(triggers, ensure_ascii=False)}
TECH STACK: {json.dumps(tech_stack, ensure_ascii=False)}
PAIN POINTS: {json.dumps(web_data.get("pain_points_detected",[]), ensure_ascii=False)}
DECISION MAKERS: {json.dumps(web_data.get("key_decision_makers",[]), ensure_ascii=False)}
FINANCIAL SIGNALS: {json.dumps(web_data.get("financial_signals",[]), ensure_ascii=False)}

RULES: Only use provided data. No fabrication. All English.
{f'Use contact name "{acct_contact}" in the speech opening.' if acct_contact else 'Do NOT use any greeting. Start directly with the opening fact.'}
{f'The sales rep says: "{acct_context}". Use this insider knowledge.' if acct_context else ''}

Generate a STRUCTURED 4-PART CLIENT SPEECH (total min 120 words):

PART 1 "OPENING FACT": A specific, verifiable fact about the company with a date from the triggers. One or two sentences max.
PART 2 "CLIENT CHALLENGE": The main IT challenge or pain point this company faces right now. Be specific and use data.
PART 3 "OPPORTUNITY BRIDGE": Connect the challenge to a conversation opportunity. Why should they talk to HPE NOW?
PART 4 "HPE SOLUTION": Name the primary product ({primary['producto_nombre']}), one concrete benefit, and include the URL. 

Also generate an INTERNAL SUMMARY (min 80 words):
Why NOW, key triggers w/ dates, all 3 recommended products, competitive landscape, urgency (HIGH/MEDIUM/LOW), next step.

JSON:
{{
    "resumen_ejecutivo": "Executive summary 2-3 sentences",
    "pain_points": ["pain 1", "pain 2"],
    "solucion_hpe_recomendada": "{primary['producto_nombre']}",
    "speech_opening": "OPENING FACT text (2 sentences max with date)",
    "speech_challenge": "CLIENT CHALLENGE text (2-3 sentences)",
    "speech_bridge": "OPPORTUNITY BRIDGE text (2-3 sentences)",
    "speech_solution": "HPE SOLUTION text (2-3 sentences with product name and URL)",
    "speech_resumen": "INTERNAL SUMMARY 80+ words with all 3 products",
    "referencia_hpe": "{primary.get('url', '')}",
    "recommendation_status": "STRONG_FIT | MODERATE_FIT | EXPLORATORY",
    "urgency": "HIGH | MEDIUM | LOW"
}}"""

    try:
        completion = groq_client.chat.completions.create(
            messages=[{"role":"system","content":system_prompt},
                      {"role":"user","content":f"Web context:\n{web_context}\n\nHPE context:\n{internal_context or 'N/A'}"}],
            model="llama-3.3-70b-versatile", temperature=0.3, response_format={"type":"json_object"})
        raw = completion.choices[0].message.content
        try: ai_json = json.loads(raw)
        except: ai_json = {"resumen_ejecutivo":"Analysis completed.","pain_points":[],
            "solucion_hpe_recomendada":primary["producto_nombre"],
            "speech_opening":raw,"speech_challenge":"","speech_bridge":"","speech_solution":"",
            "speech_resumen":"","referencia_hpe":primary.get("url",""),"recommendation_status":"EXPLORATORY","urgency":"MEDIUM"}
    except Exception as e: raise HTTPException(500, str(e))

    # Backward compat: build full speech_approach from parts
    full_speech = f"{ai_json.get('speech_opening','')}\n\n{ai_json.get('speech_challenge','')}\n\n{ai_json.get('speech_bridge','')}\n\n{ai_json.get('speech_solution','')}"
    ai_json["speech_approach"] = full_speech.strip()

    # 🔴 FIX v8.2: Obtener score previo para degradación gradual
    previous_score = None
    conn_prev = get_conn()
    prev = conn_prev.execute(
        "SELECT fit_score FROM analysis_history WHERE LOWER(company_name)=LOWER(?) ORDER BY created_at DESC LIMIT 1",
        (request.company_name,)
    ).fetchone()
    conn_prev.close()
    if prev and prev["fit_score"]:
        previous_score = prev["fit_score"]
        print(f"   📊 Previous score found: {previous_score}")
    
    score_result = calculate_score(
        triggers=triggers, tech_stack=tech_stack, industry=industry,
        product_confidence=primary.get("confidence", 0),
        financial_signals=web_data.get("financial_signals", []),
        pain_points=ai_json.get("pain_points", []),
        competitors=web_data.get("competitors", []),
        previous_score=previous_score  # 🔴 FIX: Pasar score anterior
    )
    fit_score = score_result["score"]
    
    # 🔴 DEBUG: Mostrar si hubo degradación
    if "_note" in score_result.get("breakdown", {}):
        print(f"   ⚠️  {score_result['breakdown']['_note']}")

    save_analysis({"company_name":request.company_name,"industry":industry,"fit_score":fit_score,
        "triggers":triggers,"tech_stack":tech_stack,"competitors":web_data.get("competitors",[]),
        "hpe_product":primary["producto_nombre"],"hpe_category":primary.get("categoria",""),
        "speech":ai_json.get("speech_approach",""),"resumen":ai_json.get("resumen_ejecutivo",""),
        "pain_points":ai_json.get("pain_points",[]),"target_role":request.target_role,"sources":sources_used})

    # Serialize top3 for frontend
    top3_serializable = []
    for rec in top3:
        top3_serializable.append({
            "name": rec["producto_nombre"],
            "category": rec["categoria"],
            "url": rec["url"],
            "confidence": rec["confidence"],
            "need_detected": rec["need_detected"],
            "competitive_advantage": rec["competitive_advantage"],
            "relationship": rec["relationship"],
            "pain_points": rec["pain_points"],
        })

    return {"company":request.company_name,"analysis_json":json.dumps(ai_json,ensure_ascii=False),
        "web_data":web_data,"top3_recommendations":top3_serializable,
        "fit_score":fit_score,"sources":list(set(sources_used)),"has_opportunity":True,"is_competitor":False}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
