"""
HPE Product Matcher v2 — Returns top 3 recommendations with HPE URLs
"""
import json
from pathlib import Path
from typing import List, Dict

CATALOG_PATH = Path(__file__).parent.parent / "data" / "hpe_products_catalog.json"
with open(CATALOG_PATH, 'r', encoding='utf-8') as f:
    CATALOG = json.load(f)
PRODUCTOS = {p["id"]: p for p in CATALOG["productos_hpe"]}


def _score_products(triggers: List[Dict], tech_stack: List[str] = None, industry: str = None) -> Dict[str, int]:
    scores = {pid: 0 for pid in PRODUCTOS}
    match_details = {pid: [] for pid in PRODUCTOS}

    for trigger in (triggers or []):
        trigger_text = f"{trigger.get('type', '')} {trigger.get('description', '')}".lower()
        for pid, prod in PRODUCTOS.items():
            for kw in prod["trigger_keywords"]:
                if kw.lower() in trigger_text:
                    scores[pid] += 10
                    match_details[pid].append(f"Trigger: '{kw}' in {trigger.get('type')}")
                    if trigger.get('sentiment') == 'POSITIVE':
                        scores[pid] += 5

    if industry:
        for pid, prod in PRODUCTOS.items():
            if industry in prod.get("industrias_clave", []):
                scores[pid] += 15
                match_details[pid].append(f"Industry: {industry}")

    if tech_stack:
        for pid, prod in PRODUCTOS.items():
            for tech in tech_stack:
                for comp in prod["ventajas_vs_competencia"]:
                    if comp.lower() in tech.lower():
                        scores[pid] += 20
                        match_details[pid].append(f"Competitor: {tech}")

    # Type boosts
    for trigger in (triggers or []):
        tt = trigger.get('type', '').upper()
        if 'EXPANSION' in tt or 'DATA_CENTER' in tt: scores['greenlake'] += 20
        if 'SECURITY' in tt or 'NETWORK' in tt: scores['aruba'] += 20
        if 'SERVER_REFRESH' in tt: scores['proliant'] += 20
        if 'CLOUD' in tt: scores['greenlake'] += 15
        if 'DIGITAL_TRANSFORMATION' in tt:
            scores['greenlake'] += 10; scores['aruba'] += 10

    return scores, match_details


def find_best_product(triggers: List[Dict], tech_stack: List[str] = None, industry: str = None) -> Dict:
    """Returns the single best product (backward compatible)."""
    scores, match_details = _score_products(triggers, tech_stack, industry)
    best_id = max(scores, key=scores.get)
    prod = PRODUCTOS[best_id]
    return {
        "producto_id": best_id,
        "producto_nombre": prod["nombre"],
        "categoria": prod["categoria"],
        "url": prod.get("url", ""),
        "confidence": round(min(scores[best_id] / 100, 1.0), 2),
        "reasoning": " | ".join(match_details[best_id][:3]) if match_details[best_id] else "General fit",
        "pain_points": prod["pain_points_resuelve"],
        "caso_uso": prod["caso_uso_ejemplo"],
        "speech_hook": prod["speech_hook"],
        "ventajas_vs_competencia": prod["ventajas_vs_competencia"],
    }


def find_top3_products(triggers: List[Dict], tech_stack: List[str] = None, industry: str = None) -> List[Dict]:
    """Returns top 3 HPE product recommendations, each with need, product, URL, and relationship."""
    scores, match_details = _score_products(triggers, tech_stack, industry)

    # Sort by score desc, take top 3
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]

    results = []
    for pid, score in ranked:
        prod = PRODUCTOS[pid]
        # Build "need detected" from match details
        needs = match_details[pid][:2] if match_details[pid] else ["General infrastructure needs"]
        
        # Build competitive advantage text (pick most relevant)
        comp_adv = ""
        if tech_stack:
            for tech in tech_stack:
                for comp, adv in prod["ventajas_vs_competencia"].items():
                    if comp.lower() in tech.lower():
                        comp_adv = f"vs {comp}: {adv}"
                        break
                if comp_adv: break
        if not comp_adv:
            first_comp = list(prod["ventajas_vs_competencia"].items())[0]
            comp_adv = f"vs {first_comp[0]}: {first_comp[1]}"

        results.append({
            "producto_id": pid,
            "producto_nombre": prod["nombre"],
            "categoria": prod["categoria"],
            "url": prod.get("url", ""),
            "confidence": round(min(score / 100, 1.0), 2),
            "score": score,
            "need_detected": needs,
            "pain_points": prod["pain_points_resuelve"],
            "competitive_advantage": comp_adv,
            "caso_uso": prod["caso_uso_ejemplo"],
            "speech_hook": prod["speech_hook"],
            "relationship": _build_relationship(pid, prod, triggers, tech_stack),
        })

    return results


def _build_relationship(pid: str, prod: Dict, triggers: List[Dict], tech_stack: List[str] = None) -> str:
    """Builds explicit need-to-solution relationship text."""
    parts = []
    for t in (triggers or []):
        txt = f"{t.get('type','')} {t.get('description','')}".lower()
        for kw in prod["trigger_keywords"]:
            if kw.lower() in txt:
                parts.append(f"{t.get('type','').replace('_',' ').title()} signal → {prod['nombre']} addresses this with {prod['pain_points_resuelve'][0].lower()}")
                break
        if parts: break
    if not parts:
        parts.append(f"{prod['nombre']} addresses general {prod['categoria'].lower()} needs for this account")
    return parts[0]


if __name__ == "__main__":
    triggers = [{"type": "EXPANSION", "description": "Opening new data center"}, {"type": "SECURITY_INCIDENT", "description": "Ransomware attack reported"}]
    top3 = find_top3_products(triggers, tech_stack=["Cisco"], industry="Manufacturing")
    for i, r in enumerate(top3):
        print(f"{i+1}. {r['producto_nombre']} (score:{r['score']}) — {r['url']}")
        print(f"   Need: {r['need_detected']}")
        print(f"   Relationship: {r['relationship']}")
