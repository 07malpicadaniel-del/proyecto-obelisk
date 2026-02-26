@echo off
REM Script para hacer commit y push de los cambios con documentación

echo.
echo ========================================
echo   SUBIR CAMBIOS A GITHUB
echo ========================================
echo.

REM 1. Verificar rama actual
echo [1/5] Verificando rama actual...
git branch --show-current
echo.

REM 2. Add archivos
echo [2/5] Agregando archivos modificados...
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
echo.

REM 3. Mostrar status
echo [3/5] Archivos a commitear:
git status --short
echo.

REM 4. Commit
echo [4/5] Creando commit...
git commit -F COMMIT_MESSAGE.txt
echo.

REM 5. Push
echo [5/5] Subiendo a GitHub...
git push
echo.

echo ========================================
echo   COMPLETADO
echo ========================================
echo.
echo Proximos pasos:
echo 1. Ve a GitHub
echo 2. Crea un Pull Request
echo 3. Copia PULL_REQUEST.md en la descripcion
echo 4. Solicita reviews
echo.
pause
