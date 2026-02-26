#!/usr/bin/env python3
"""
Script para aplicar el fix de previous_score a scanner.py
"""

# Ruta
SCANNER_PATH = r"C:\Users\R-Cou\Escritorio\CLAUDE COSAS\Innovation2\backend\scanner.py"

print("🔧 Aplicando fix de previous_score a scanner.py...")

# Leer archivo
with open(SCANNER_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

# Buscar la llamada a calculate_score
old_code = """    score_result = calculate_score(
        triggers=current_triggers, tech_stack=tech_stack, industry=industry,
        product_confidence=confidence,
        financial_signals=web_data.get("financial_signals", []),
        pain_points=web_data.get("pain_points_detected", []),
        competitors=web_data.get("competitors", [])
    )"""

new_code = """    score_result = calculate_score(
        triggers=current_triggers, tech_stack=tech_stack, industry=industry,
        product_confidence=confidence,
        financial_signals=web_data.get("financial_signals", []),
        pain_points=web_data.get("pain_points_detected", []),
        competitors=web_data.get("competitors", []),
        previous_score=previous_score  # 🔴 FIX v8.2: Pasar score anterior para degradación gradual
    )"""

# Aplicar cambio
if old_code in content:
    content = content.replace(old_code, new_code)
    print("✅ Fix aplicado correctamente")
    
    # Guardar
    with open(SCANNER_PATH, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"💾 Archivo guardado: {SCANNER_PATH}")
    print("\n✅ ¡scanner.py actualizado!")
else:
    print("❌ No se encontró el código a reemplazar")
    print("Puede que ya esté aplicado o que el archivo sea diferente")
