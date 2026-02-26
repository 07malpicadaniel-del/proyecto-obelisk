#!/bin/bash
# Script para hacer commit y push de los cambios con documentación

echo "🚀 Preparando commit con toda la documentación..."

# 1. Verificar que estamos en la rama correcta
CURRENT_BRANCH=$(git branch --show-current)
echo "📍 Rama actual: $CURRENT_BRANCH"

# 2. Add todos los archivos modificados
echo "📦 Agregando archivos..."
git add backend/scoring.py
git add backend/web_agent.py
git add frontend/src/App.tsx
git add CHANGELOG.md
git add GUIA_EQUIPO.md
git add PULL_REQUEST.md
git add COMMIT_MESSAGE.txt
git add INSTRUCCIONES_SIMPLES.md
git add ARCHIVOS_LISTOS.md
git add aplicar_correcciones.py

# 3. Mostrar status
echo ""
echo "📋 Archivos a commitear:"
git status --short

# 4. Commit con mensaje detallado
echo ""
echo "💾 Creando commit..."
git commit -F COMMIT_MESSAGE.txt

# 5. Push
echo ""
echo "🌐 Pushing a GitHub..."
git push origin $CURRENT_BRANCH

echo ""
echo "✅ ¡Listo! Cambios subidos a GitHub"
echo ""
echo "📝 Próximos pasos:"
echo "1. Ve a GitHub y crea un Pull Request"
echo "2. Copia el contenido de PULL_REQUEST.md en la descripción"
echo "3. Solicita reviews de @frontend-lead y @backend-lead"
echo ""
