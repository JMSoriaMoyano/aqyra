@echo off
REM ============================================================
REM  Aqyra - Fase 0 git LOCAL (NO sube nada a la nube)
REM  Inicializa git en Entorno, Aqyra-Raiz y Estructurando 2.0,
REM  respetando .gitignore (excluye node_modules, .env, *.plugin...).
REM  Estructurando NO se toca (ya es repo).
REM  Doble clic. Resultado en ..\FASE0_git_resultado.txt
REM ============================================================
setlocal
set "LOG=%~dp0..\FASE0_git_resultado.txt"
echo Aqyra Fase 0 git local - %date% %time% > "%LOG%"
echo (NO sube nada; solo crea el historial local) >> "%LOG%"

echo ===== Entorno ===== >> "%LOG%"
cd /d "%~dp0.."
if exist "Entorno\.git" rmdir /s /q "Entorno\.git"
cd /d "%~dp0..\Entorno"
git init -b main >> "%LOG%" 2>&1
git config user.email "jmsoria@ciccp.es"
git config user.name "JM Soria"
git add -A >> "%LOG%" 2>&1
git commit -m "chore: init repo + .gitignore (Fase 0)" >> "%LOG%" 2>&1
echo -- ficheros versionados (Entorno): >> "%LOG%"
git ls-files | find /c /v "" >> "%LOG%"
echo -- check .env (debe imprimir la ruta = ignorado): >> "%LOG%"
git check-ignore publico\demo\.env >> "%LOG%" 2>&1
echo -- check node_modules colado (debe estar vacio): >> "%LOG%"
git ls-files | findstr /i "node_modules" >> "%LOG%"

echo ===== Aqyra-Raiz ===== >> "%LOG%"
cd /d "%~dp0."
git init -b main >> "%LOG%" 2>&1
git config user.email "jmsoria@ciccp.es"
git config user.name "JM Soria"
git add -A >> "%LOG%" 2>&1
git commit -m "chore: init repo + .gitignore (Fase 0)" >> "%LOG%" 2>&1
echo -- ficheros versionados (Aqyra-Raiz): >> "%LOG%"
git ls-files | find /c /v "" >> "%LOG%"

echo ===== Estructurando 2.0 ===== >> "%LOG%"
cd /d "%~dp0..\Estructurando 2.0"
git init -b main >> "%LOG%" 2>&1
git config user.email "jmsoria@ciccp.es"
git config user.name "JM Soria"
git add -A >> "%LOG%" 2>&1
git commit -m "chore: init repo + .gitignore (Fase 0)" >> "%LOG%" 2>&1
echo -- ficheros versionados (Estructurando 2.0): >> "%LOG%"
git ls-files | find /c /v "" >> "%LOG%"

echo ===== FIN ===== >> "%LOG%"
echo.
echo Listo. Resultado en FASE0_git_resultado.txt (carpeta Projects).
pause
