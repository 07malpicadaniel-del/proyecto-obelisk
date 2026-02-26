"""
scoring.py — Intelligent Opportunity Scoring for HPE Sales Guardian
Produces meaningful scores from 0-100 based on signal quality, not just quantity.

🔴 FIX v8.2: Graceful degradation when no new triggers found
"""

# Trigger types ranked by value to HPE sales
TRIGGER_WEIGHTS = {
    "DATA_CENTER": 12,          # Direct infrastructure need
    "SERVER_REFRESH": 11,       # Direct compute need
    "CLOUD_MIGRATION": 10,      # GreenLake opportunity
    "NETWORK_UPGRADE": 9,       # Aruba opportunity
    "SECURITY_INCIDENT": 8,     # Zero Trust conversation
    "DIGITAL_TRANSFORMATION": 7,# Broad opportunity
    "EXPANSION": 6,             # Growth = budget
    "COMPETITOR_CONTRACT": 5,   # Displacement play
    "LEADERSHIP_CHANGE": 3,     # New decision maker, not a need itself
}

# Tech stack items that indicate HPE-relevant infrastructure
HPE_RELEVANT_TECH = {
    "vmware", "kubernetes", "docker", "aws", "azure", "gcp", "linux",
    "windows server", "sql server", "oracle", "sap", "cisco", "dell",
    "nutanix", "red hat", "splunk", "palo alto", "crowdstrike",
}


def calculate_score(triggers: list, tech_stack: list, industry: str,
                    product_confidence: float, financial_signals: list = None,
                    pain_points: list = None, competitors: list = None,
                    previous_score: int = None) -> dict:
    """
    Calculate a meaningful opportunity score from 0-100.
    Returns dict with score, breakdown, and label.
    
    Args:
        previous_score: Previous score for graceful degradation when no new triggers
    """
    breakdown = {}

    # 🔴 FIX: Si no hay triggers pero existía un score previo, degradar gradualmente
    if len(triggers) == 0 and previous_score is not None and previous_score > 0:
        # Degradación suave: máximo -10 puntos por ciclo
        degraded_score = max(30, previous_score - 10)  # Piso en 30 vs 5 original
        breakdown["triggers"] = 0
        breakdown["tech_stack"] = 0
        breakdown["product_match"] = 0
        breakdown["financial"] = 0
        breakdown["pain_points"] = 0
        breakdown["competitive"] = 0
        breakdown["_note"] = "No new triggers - score degraded from previous"
        
        return {
            "score": degraded_score,
            "label": "DEGRADED" if degraded_score < 60 else "MODERATE",
            "breakdown": breakdown,
            "trigger_count": 0,
            "trigger_types": [],
        }

    # ── 1. Trigger Score (max 40 pts) ─────────────────────────────────────
    trigger_points = 0
    trigger_types_seen = set()
    dated_count = 0

    for t in triggers:
        ttype = t.get("type", "UNKNOWN")
        weight = TRIGGER_WEIGHTS.get(ttype, 2)

        # First occurrence of a type is worth full weight
        if ttype not in trigger_types_seen:
            trigger_points += weight
            trigger_types_seen.add(ttype)
        else:
            # Diminishing returns for duplicate types
            trigger_points += weight * 0.3

        # Bonus for dated triggers (more credible)
        if t.get("date"):
            dated_count += 1

    # Diversity bonus: more different types = better
    diversity_bonus = min(5, len(trigger_types_seen) * 1.5)
    trigger_points += diversity_bonus

    # Recency bonus for dated signals
    if dated_count >= 3:
        trigger_points += 3
    elif dated_count >= 1:
        trigger_points += 1

    trigger_score = min(40, trigger_points)
    breakdown["triggers"] = round(trigger_score, 1)

    # ── 2. Tech Stack Relevance (max 15 pts) ─────────────────────────────
    relevant_count = 0
    for tech in tech_stack:
        tech_lower = tech.lower().strip()
        for relevant in HPE_RELEVANT_TECH:
            if relevant in tech_lower or tech_lower in relevant:
                relevant_count += 1
                break

    # Score based on how many relevant techs vs total
    if tech_stack:
        relevance_ratio = relevant_count / len(tech_stack)
        tech_score = min(15, relevant_count * 3 + relevance_ratio * 5)
    else:
        tech_score = 0
    breakdown["tech_stack"] = round(tech_score, 1)

    # ── 3. Product Match Confidence (max 20 pts) ─────────────────────────
    confidence_score = min(20, product_confidence * 20)
    breakdown["product_match"] = round(confidence_score, 1)

    # ── 4. Financial Signals (max 10 pts) ─────────────────────────────────
    fin_signals = financial_signals or []
    fin_score = min(10, len(fin_signals) * 3)
    breakdown["financial"] = round(fin_score, 1)

    # ── 5. Pain Points (max 10 pts) ──────────────────────────────────────
    pp = pain_points or []
    pp_score = min(10, len(pp) * 2.5)
    breakdown["pain_points"] = round(pp_score, 1)

    # ── 6. Competitive Intelligence (max 5 pts) ──────────────────────────
    comps = competitors or []
    comp_score = min(5, len(comps) * 1.5) if comps else 0
    breakdown["competitive"] = round(comp_score, 1)

    # ── Total ────────────────────────────────────────────────────────────
    raw_total = trigger_score + tech_score + confidence_score + fin_score + pp_score + comp_score
    
    # 🔴 FIX: Piso mínimo aumentado de 5 → 10 para nuevas empresas
    # Empresas con historial tienen piso de 30 (ver arriba)
    total = max(10, min(100, round(raw_total)))

    # Label
    if total >= 80:
        label = "CRITICAL"
    elif total >= 60:
        label = "HIGH"
    elif total >= 40:
        label = "MODERATE"
    elif total >= 20:
        label = "LOW"
    else:
        label = "MINIMAL"

    return {
        "score": total,
        "label": label,
        "breakdown": breakdown,
        "trigger_count": len(triggers),
        "trigger_types": list(trigger_types_seen),
    }
