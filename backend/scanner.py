"""
scanner.py — Background Account Scanner (Flight Radar Mode)
Periodically re-scans all accounts, detects NEW triggers, and generates alerts.
"""
import json
import sqlite3
import traceback
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple

DB_PATH = Path(__file__).parent.parent / "data" / "obelisk.db"


def get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def _get_previous_triggers(company_name: str) -> set:
    """Get set of trigger descriptions from last analysis."""
    conn = get_conn()
    row = conn.execute(
        "SELECT triggers FROM analysis_history WHERE LOWER(company_name)=LOWER(?) ORDER BY created_at DESC LIMIT 1",
        (company_name,)
    ).fetchone()
    conn.close()
    if not row or not row["triggers"]:
        return set()
    try:
        triggers = json.loads(row["triggers"])
        return {t.get("description", "").lower().strip() for t in triggers if t.get("description")}
    except:
        return set()


def _get_previous_score(company_name: str) -> int:
    conn = get_conn()
    row = conn.execute(
        "SELECT fit_score FROM analysis_history WHERE LOWER(company_name)=LOWER(?) ORDER BY created_at DESC LIMIT 1",
        (company_name,)
    ).fetchone()
    conn.close()
    return row["fit_score"] if row else 0


def scan_account(company_name: str) -> Dict:
    """
    Scan a single account for new signals.
    Returns dict with: new_triggers, score_change, alert_level, summary
    """
    from web_agent import search_and_structure
    from product_matcher import find_top3_products
    from scoring import calculate_score

    previous_triggers = _get_previous_triggers(company_name)
    previous_score = _get_previous_score(company_name)

    # Run web search
    web_data = search_and_structure(company_name)

    if web_data.get("is_hpe_competitor", False):
        return {"company": company_name, "status": "COMPETITOR", "new_triggers": [], "alert_level": "NONE"}

    current_triggers = web_data.get("triggers", [])
    tech_stack = web_data.get("tech_stack", [])
    industry = web_data.get("industry", "")

    # Detect NEW triggers (not seen before)
    new_triggers = []
    for t in current_triggers:
        desc = t.get("description", "").lower().strip()
        if desc and desc not in previous_triggers:
            new_triggers.append(t)

    # Calculate score
    top3 = find_top3_products(current_triggers, tech_stack, industry)
    primary = top3[0] if top3 else None
    confidence = primary.get("confidence", 0) if primary else 0
    score_result = calculate_score(
        triggers=current_triggers, tech_stack=tech_stack, industry=industry,
        product_confidence=confidence,
        financial_signals=web_data.get("financial_signals", []),
        pain_points=web_data.get("pain_points_detected", []),
        competitors=web_data.get("competitors", []),
        previous_score=previous_score  # 🔴 FIX v8.2: Pasar score anterior para degradación gradual
    )
    fit_score = score_result["score"]

    score_change = fit_score - previous_score

    # Determine alert level
    if len(new_triggers) >= 3 or score_change >= 15:
        alert_level = "HIGH"
    elif len(new_triggers) >= 1 or score_change >= 5:
        alert_level = "MEDIUM"
    elif score_change < -10:
        alert_level = "LOW"  # Score dropped
    else:
        alert_level = "NONE"

    # Build summary
    if new_triggers:
        trigger_types = list(set(t.get("type", "UNKNOWN") for t in new_triggers))
        summary = f"{len(new_triggers)} new signal(s) detected: {', '.join(t.replace('_',' ').title() for t in trigger_types[:3])}"
    elif score_change > 0:
        summary = f"Score increased +{score_change} points"
    elif score_change < -10:
        summary = f"Score decreased {score_change} points — signals may be aging"
    else:
        summary = "No significant changes detected"

    # Save to analysis history if there are new signals
    if new_triggers or score_change != 0:
        try:
            conn = get_conn()
            conn.execute("""INSERT INTO analysis_history 
                (company_name,industry,fit_score,triggers,tech_stack,competitors,
                 hpe_product_recommended,hpe_product_category,speech,resumen,pain_points,target_role,sources)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (company_name, industry, fit_score,
                 json.dumps(current_triggers, ensure_ascii=False),
                 json.dumps(tech_stack, ensure_ascii=False),
                 json.dumps(web_data.get("competitors", []), ensure_ascii=False),
                 primary["producto_nombre"] if primary else "",
                 primary.get("categoria", "") if primary else "",
                 "",  # No speech in auto-scan
                 summary,
                 json.dumps(web_data.get("pain_points_detected", []), ensure_ascii=False),
                 "AUTO_SCAN",
                 json.dumps(["Auto Scanner"], ensure_ascii=False)))
            conn.execute("""UPDATE accounts SET last_score=?, last_product=?, last_status=?,
                industry=?, updated_at=datetime('now') WHERE LOWER(company_name)=LOWER(?)""",
                (fit_score, primary["producto_nombre"] if primary else "", "ANALYZED",
                 industry, company_name))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[SCANNER] DB save error for {company_name}: {e}")

    return {
        "company": company_name,
        "status": "SCANNED",
        "fit_score": fit_score,
        "previous_score": previous_score,
        "score_change": score_change,
        "new_triggers": [{"type": t.get("type"), "description": t.get("description"), "date": t.get("date")} for t in new_triggers],
        "total_triggers": len(current_triggers),
        "alert_level": alert_level,
        "summary": summary,
        "recommended_product": primary["producto_nombre"] if primary else None,
        "top3": [r["producto_nombre"] for r in top3] if top3 else [],
    }


def scan_all_accounts() -> List[Dict]:
    """Scan all accounts in the database. Returns list of scan results."""
    conn = get_conn()
    accounts = conn.execute("SELECT id, company_name FROM accounts ORDER BY updated_at ASC").fetchall()
    conn.close()

    results = []
    print(f"\n{'='*60}")
    print(f"[SCANNER] Starting full scan — {len(accounts)} accounts — {datetime.now().isoformat()}")
    print(f"{'='*60}")

    for acc in accounts:
        company = acc["company_name"]
        try:
            print(f"[SCANNER] Scanning: {company}...")
            result = scan_account(company)
            results.append(result)

            # Save alert if meaningful
            if result["alert_level"] != "NONE":
                _save_alert(acc["id"], company, result)
                print(f"[SCANNER]   → ALERT {result['alert_level']}: {result['summary']}")
            else:
                print(f"[SCANNER]   → No changes")

        except Exception as e:
            print(f"[SCANNER]   → ERROR: {e}")
            traceback.print_exc()
            results.append({"company": company, "status": "ERROR", "alert_level": "NONE", "summary": str(e)})

    print(f"[SCANNER] Scan complete. {sum(1 for r in results if r['alert_level'] != 'NONE')} alerts generated.\n")
    return results


def _save_alert(account_id: int, company_name: str, scan_result: Dict):
    """Save alert to alerts table."""
    conn = get_conn()
    conn.execute("""INSERT INTO alerts 
        (account_id, company_name, alert_level, summary, new_triggers, score_change, fit_score, recommended_product)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (account_id, company_name, scan_result["alert_level"], scan_result["summary"],
         json.dumps(scan_result.get("new_triggers", []), ensure_ascii=False),
         scan_result.get("score_change", 0), scan_result.get("fit_score", 0),
         scan_result.get("recommended_product", "")))
    conn.commit()
    conn.close()


if __name__ == "__main__":
    results = scan_all_accounts()
    for r in results:
        flag = "🔴" if r["alert_level"] == "HIGH" else "🟡" if r["alert_level"] == "MEDIUM" else "⚪"
        print(f"  {flag} {r['company']}: {r['summary']}")
