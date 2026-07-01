@echo off
REM ============================================================
REM  Aqyra - Fase 1: conectar y SUBIR a GitHub (repos PRIVADOS)
REM  REQUISITO: haber creado antes en github.com/JMSoriaMoyano
REM  los repos VACIOS: aqyra-entorno, aqyra-raiz, aqyra-contratos-golden
REM  (Private, SIN README/.gitignore/license).
REM  La primera subida abrira el navegador para iniciar sesion (tu auth).
REM  Estructurando (aqyra-motor) NO se sube aqui (tiene cambios pendientes).
REM  Doble clic. Resultado en ..\FASE1_git_resultado.txt
REM ============================================================
setlocal
set "U=JMSoriaMoyano"
set "LOG=%~dp0..\FASE1_git_resultado.txt"
echo Aqyra Fase 1 push - %date% %time% > "%LOG%"

echo ===== Entorno : aqyra-entorno ===== >> "%LOG%"
cd /d "%~dp0..\Entorno"
git remote remove origin 2>nul
git remote add origin https://github.com/%U%/aqyra-entorno.git
git branch -M main
git push -u origin main >> "%LOG%" 2>&1

echo ===== Aqyra-Raiz : aqyra-raiz ===== >> "%LOG%"
cd /d "%~dp0."
git remote remove origin 2>nul
git remote add origin https://github.com/%U%/aqyra-raiz.git
git branch -M main
git push -u origin main >> "%LOG%" 2>&1

echo ===== Estructurando 2.0 : aqyra-contratos-golden ===== >> "%LOG%"
cd /d "%~dp0..\Estructurando 2.0"
git remote remove origin 2>nul
git remote add origin https://github.com/%U%/aqyra-contratos-golden.git
git branch -M main
git push -u origin main >> "%LOG%" 2>&1

echo ===== FIN ===== >> "%LOG%"
echo.
echo Listo. Revisa FASE1_git_resultado.txt (carpeta Projects).
pause
