"""
scoring.py — Intelligent Opportunity Scoring for HPE Sales Guardian (FIXED)
🔴 FIX: Score degradation instead of collapse when triggers == 0
"""

# Trigger types ranked by value to HPE sales
TRIGGER_WEIGHTS = {
    "DATA_CENTER": 12,
    "SERVER_REFRESH": 11,
    "CLOUD_MIGRATION": 10,
    "NETWORK_UPGRADE": 9,
    "SECURITY_INCIDENT": 8,
    "DIGITAL_TRANSFORMATION": 7,
    "EXPANSION": 6,
    "COMPETITOR_CONTRACT": 5,
    "LEADERSHIP_CHANGE": 3,
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
    
    🔴 FIXED: No longer collapses to 5 when triggers == 0
    - If no NEW triggers but had previous score → degrade gracefully by max 10 points
    - Minimum floor is now 30 instead of 5 (if there was previous activity)
    
    Returns dict with score, breakdown, and label.
    """
    breakdown = {}

    # ── 1. Trigger Score (max 40 pts) ─────────────────────────────────────
    trigger_points = 0
    trigger_types_seen = set()
    dated_count = 0

    for t in triggers:
        ttype = t.get("type", "UNKNOWN")
        weight = TRIGGER_WEIGHTS.get(ttype, 2)

        if ttype not in trigger_types_seen:
            trigger_points += weight
            trigger_types_seen.add(ttype)
        else:
            trigger_points += weight * 0.3

        if t.get("date"):
            dated_count += 1

    diversity_bonus = min(5, len(trigger_types_seen) * 1.5)
    trigger_points += diversity_bonus

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

    # 🔴 FIX: Graceful degradation instead of collapse
    if len(triggers) == 0 and previous_score is not None and previous_score > 0:
        # No new triggers, but there was previous activity
        # Degrade by max 10 points, but keep at least 30 as floor
        degraded_score = max(30, previous_score - 10)
        total = min(100, degraded_score)
        breakdown["_note"] = "No new triggers - score degraded from previous"
    else:
        # Normal calculation
        # Minimum is 10 instead of 5 (more realistic for real companies)
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
