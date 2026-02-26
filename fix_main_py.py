#!/usr/bin/env python3
"""
Script para aplicar el fix de previous_score a main.py
"""
import re

# Ruta
MAIN_PATH = r"C:\Users\R-Cou\Escritorio\CLAUDE COSAS\Innovation2\backend\main.py"

print("🔧 Aplicando fix de previous_score a main.py...")

# Leer archivo
with open(MAIN_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

# Buscar la llamada a calculate_score
old_code = """    score_result = calculate_score(
        triggers=triggers, tech_stack=tech_stack, industry=industry,
        product_confidence=primary.get("confidence", 0),
        financial_signals=web_data.get("financial_signals", []),
        pain_points=ai_json.get("pain_points", []),
        competitors=web_data.get("competitors", [])
    )
    fit_score = score_result["score"]"""

new_code = """    # 🔴 FIX v8.2: Obtener score previo para degradación gradual
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
        print(f"   ⚠️  {score_result['breakdown']['_note']}")"""

# Aplicar cambio
if old_code in content:
    content = content.replace(old_code, new_code)
    print("✅ Fix aplicado correctamente")
    
    # Guardar
    with open(MAIN_PATH, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"💾 Archivo guardado: {MAIN_PATH}")
    print("\n✅ ¡LISTO! Ahora reinicia el backend:")
    print("   cd backend")
    print("   python main.py")
else:
    print("❌ No se encontró el código a reemplazar")
    print("Puede que ya esté aplicado o que el archivo sea diferente")
