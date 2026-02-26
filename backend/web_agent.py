"""
web_agent.py — Web Research Agent for HPE Sales Guardian
Focused on IT infrastructure buying signals.
Primary: SerpAPI (Google) | Fallback: DuckDuckGo
"""
import os
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
SERP_API_KEY = os.getenv("SERP_API_KEY")

# ── HPE Direct Competitors ───────────────────────────────────────────────────
HPE_DIRECT_COMPETITORS = {
    "amazon", "aws", "amazon web services",
    "dell", "dell technologies", "dell emc",
    "cisco", "cisco systems",
    "lenovo",
    "ibm",
    "oracle",
    "nutanix",
    "pure storage",
    "netapp",
    "vmware", "broadcom vmware",
    "supermicro", "super micro",
}

HPE_OWN_NAMES = {
    "hpe", "hewlett packard enterprise", "hewlett-packard enterprise",
    "hp enterprise", "aruba", "aruba networks",
    "greenlake", "hpe greenlake",
    "proliant", "hpe proliant",
    "alletra", "hpe alletra",
}


def _is_hpe_competitor(company_name: str) -> bool:
    name_lower = company_name.strip().lower()
    for comp in HPE_DIRECT_COMPETITORS:
        if comp in name_lower or name_lower in comp:
            return True
    return False


def _clean_competitors_list(competitors: list, company_name: str) -> list:
    cleaned = []
    company_lower = company_name.strip().lower()
    for c in competitors:
        c_lower = c.strip().lower()
        if any(hpe_name in c_lower for hpe_name in HPE_OWN_NAMES):
            continue
        if c_lower in company_lower or company_lower in c_lower:
            continue
        cleaned.append(c)
    return cleaned


# ── Search Queries ────────────────────────────────────────────────────────────
def _build_queries(company: str) -> list[str]:
    return [
        f'"{company}" "new data center" OR "data center expansion" OR "cloud migration" OR "infrastructure investment"',
        f'"{company}" cybersecurity breach OR "network upgrade" OR "zero trust" OR ransomware attack',
        f'"{company}" "digital transformation" OR "IT modernization" OR "server refresh" OR "legacy systems"',
        f'"{company}" "new headquarters" OR "new plant" OR "new office" OR acquisition OR "opening facility"',
        f'"{company}" new CIO OR "new CTO" OR "chief technology officer" OR "IT director" appointed OR hired',
        f'"{company}" technology contract OR "IT vendor" OR "cloud provider" OR "infrastructure partner"',
    ]


def _search_serpapi(company: str) -> list[dict]:
    if not SERP_API_KEY:
        return []
    try:
        from serpapi import GoogleSearch
        all_results = []
        for q in _build_queries(company):
            params = {
                "q": q, "api_key": SERP_API_KEY,
                "num": 5, "hl": "en", "tbs": "qdr:m3",
            }
            search = GoogleSearch(params)
            data = search.get_dict()
            for r in data.get("organic_results", [])[:4]:
                all_results.append({
                    "title": r.get("title", ""),
                    "body": r.get("snippet", ""),
                    "href": r.get("link", ""),
                    "date": r.get("date", ""),
                })
            for n in data.get("news_results", [])[:2]:
                all_results.append({
                    "title": n.get("title", ""),
                    "body": n.get("snippet", ""),
                    "href": n.get("link", ""),
                    "date": n.get("date", ""),
                })
        seen = set()
        unique = []
        for r in all_results:
            key = r["title"].strip().lower()
            if key not in seen:
                seen.add(key)
                unique.append(r)
        print(f"   ✅ SerpAPI: {len(unique)} unique results")
        return unique
    except Exception as e:
        print(f"   ⚠️ SerpAPI failed: {e}")
        return []


def _search_duckduckgo(company: str) -> list[dict]:
    """
    🔴 FIXED: Updated to use new duckduckgo_search API (v6+)
    Silences RuntimeWarning about deprecated import
    """
    try:
        # Try new import first (v6+)
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            # Fallback to old import
            from duckduckgo_search import ddg
            DDGS = ddg
        
        all_results = []
        queries = [
            f"{company} new data center cloud infrastructure investment",
            f"{company} cybersecurity breach network upgrade",
            f"{company} digital transformation IT modernization",
            f"{company} new CIO CTO technology leadership hired",
        ]
        
        ddgs = DDGS()
        for q in queries:
            try:
                results = ddgs.text(q, max_results=4, timelimit="m")
                all_results.extend(results or [])
            except Exception as qe:
                # Silently continue if one query fails
                continue
        
        seen = set()
        unique = []
        for r in all_results:
            key = r.get("title", "").strip().lower()
            if key and key not in seen:
                seen.add(key)
                unique.append(r)
        
        print(f"   ✅ DuckDuckGo: {len(unique)} unique results")
        return unique
    except Exception as e:
        print(f"   ⚠️ DuckDuckGo failed: {e}")
        return []


def search_and_structure(company_name: str) -> dict:
    print(f"🕵️ AGENT: Researching '{company_name}'...")

    is_competitor = _is_hpe_competitor(company_name)
    if is_competitor:
        print(f"   ⚠️ {company_name} is a DIRECT HPE COMPETITOR")

    results = _search_serpapi(company_name)
    source = "SerpAPI (Google)"
    if not results:
        print("   ↳ Falling back to DuckDuckGo...")
        results = _search_duckduckgo(company_name)
        source = "DuckDuckGo"

    empty_response = {
        "raw_context": "", "triggers": [], "tech_stack": [],
        "competitors": [], "key_decision_makers": [],
        "financial_signals": [], "pain_points_detected": [],
        "industry": "Unknown",
        "fit_score_reasoning": "Insufficient information to evaluate.",
        "has_useful_signals": False, "is_hpe_competitor": is_competitor,
        "_source": source,
    }

    if not results:
        print("   ❌ No results from any source")
        return empty_response

    raw_text = "\n".join(
        [f"- [{r.get('date', 'No date')}] {r.get('title', '')}: {r.get('body', r.get('snippet', ''))}" for r in results]
    )

    system_prompt = f"""
You are a B2B commercial intelligence analyst. Your client is HPE (Hewlett Packard Enterprise).
You are analyzing "{company_name}" as a POTENTIAL CUSTOMER for HPE.

CRITICAL CONTEXT:
- HPE SELLS IT infrastructure (servers, storage, networking, hybrid cloud, AI).
- You are looking for signals that "{company_name}" NEEDS TO BUY IT infrastructure.
- "{company_name}" is NOT HPE. HPE is the seller. "{company_name}" is the potential buyer.

TODAY'S DATE: February 20, 2026. Only include information from the LAST 3 MONTHS (December 2025 — February 2026).
DISCARD any information dated before December 2025.

STRICT RULES:
1. ONLY extract information EXPLICITLY mentioned in the provided text.
2. DO NOT invent, assume, or infer data not present in the text.
3. DISCARD any trigger or signal older than 3 months. If the date is before December 2025, do NOT include it.
4. If a field has no verifiable data, leave it as empty list [] or empty string "".
5. NEVER put "HPE", "Hewlett Packard Enterprise", "Aruba", "GreenLake", "ProLiant" or "Alletra" in the competitors list.
5. In "competitors" only list companies that COMPETE WITH HPE to sell to "{company_name}" (Dell, Cisco, Lenovo, IBM, etc.)
6. Triggers must be about "{company_name}" BUYING or NEEDING technology, NOT about them SELLING technology.
7. If "{company_name}" is a tech company, distinguish between their operations as PROVIDER vs their INTERNAL infrastructure needs.
8. A trigger ONLY counts if "{company_name}" is the BUYER/USER of the technology, not the seller.
9. "has_useful_signals" must be false if there is not at least 1 trigger where "{company_name}" NEEDS to buy infrastructure.
10. EVERY trigger MUST include a date. Extract the date from the source text. If no exact date is available, use the approximate timeframe (e.g., "Q1 2025", "Early 2026", "January 2025"). If absolutely no date can be determined, use "Recent".

VALID TRIGGER TYPES (only when the company is the BUYER):
- DATA_CENTER: Building/expanding THEIR OWN data centers
- CLOUD_MIGRATION: Migrating THEIR infrastructure to hybrid cloud
- SECURITY_INCIDENT: Suffered breach/attack (needs security)
- NETWORK_UPGRADE: Modernizing THEIR internal network
- SERVER_REFRESH: Refreshing THEIR servers, end-of-life equipment
- LEADERSHIP_CHANGE: New CIO/CTO IN THE COMPANY (buying window)
- EXPANSION: Opening new plant/office/HQ (needs new infra)
- DIGITAL_TRANSFORMATION: Internal IT modernization project
- COMPETITOR_CONTRACT: Has contract with HPE competitor (displacement opportunity)

NOT VALID TRIGGERS:
- The company SELLING cloud/IT services to others
- Marketing, product, or service news about what the company OFFERS
- Generic financial reports unrelated to IT PURCHASES
- News where HPE sells to them (already happened)

RESPOND IN ENGLISH. JSON format:
{{
    "industry": "Company industry",
    "tech_stack": ["ONLY technologies the company USES internally"],
    "competitors": ["ONLY companies competing with HPE to sell to this account — NEVER include HPE"],
    "triggers": [
        {{
            "type": "TRIGGER_TYPE",
            "description": "Clear description of why this signals a need to BUY infrastructure",
            "date": "Date or timeframe from the source (e.g., 'January 2025', 'Q4 2025', 'Recent')",
            "sentiment": "POSITIVE | NEGATIVE | NEUTRAL",
            "source_snippet": "Exact phrase from text supporting this trigger"
        }}
    ],
    "key_decision_makers": ["Name — Title (only if mentioned)"],
    "financial_signals": ["Only financial signals indicating CAPACITY or INTENT to invest in IT"],
    "pain_points_detected": ["Only IT problems HPE could solve"],
    "fit_score_reasoning": "Honest assessment as potential HPE CUSTOMER",
    "has_useful_signals": true/false
}}
"""

    try:
        completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Company to analyze as potential customer: {company_name}\n\nSearch results:\n{raw_text}"},
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.05,
            response_format={"type": "json_object"},
        )

        structured = json.loads(completion.choices[0].message.content)
        structured["raw_context"] = raw_text
        structured["_source"] = source
        structured["is_hpe_competitor"] = is_competitor

        if "competitors" in structured:
            structured["competitors"] = _clean_competitors_list(structured["competitors"], company_name)

        n_triggers = len(structured.get("triggers", []))
        has_signals = structured.get("has_useful_signals", n_triggers > 0)
        structured["has_useful_signals"] = has_signals

        print(f"   {'✅' if has_signals else '⚠️'} {n_triggers} triggers | Source: {source}")
        return structured

    except Exception as e:
        print(f"   🔥 Structuring error: {e}")
        empty_response["raw_context"] = raw_text
        return empty_response
