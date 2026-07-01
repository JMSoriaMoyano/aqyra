@echo off
REM ============================================================
REM  Aqyra - Fase 1: COMMIT + SUBIR los 3 repos restantes (PRIVADOS)
REM    Entorno            -> github.com/JMSoriaMoyano/aqyra-entorno
REM    Aqyra-Raiz         -> github.com/JMSoriaMoyano/aqyra-raiz
REM    Estructurando 2.0  -> github.com/JMSoriaMoyano/aqyra-contratos-golden
REM  REQUISITO: los 3 repos ya creados VACIOS en GitHub (Private, sin README).
REM  Doble clic. La primera subida abrira el navegador para tu login.
REM  Resultado en: ..\FASE1_git_resultado_3repos.txt
REM ============================================================
setlocal
set "U=JMSoriaMoyano"
set "LOG=%~dp0..\FASE1_git_resultado_3repos.txt"
echo Aqyra Fase 1 push 3 repos - %date% %time% > "%LOG%"

call :REPO "%~dp0..\Entorno"            aqyra-entorno
call :REPO "%~dp0..\Aqyra-Raiz"         aqyra-raiz
call :REPO "%~dp0..\Estructurando 2.0"  aqyra-contratos-golden

echo ===== FIN ===== >> "%LOG%"
echo.
echo Listo. Revisa FASE1_git_resultado_3repos.txt (carpeta Projects).
pause
exit /b

:REPO
cd /d "%~1"
echo. >> "%LOG%"
echo ===== %~1  ^-^>  %2 ===== >> "%LOG%"
if exist ".git\index.lock" del /f /q ".git\index.lock"
if exist ".__write_test" del /f /q ".__write_test"
git add -A >> "%LOG%" 2>&1
git commit -m "Fase 1: commit de cambios pendientes antes de subir a la nube privada" >> "%LOG%" 2>&1
git branch -M main >> "%LOG%" 2>&1
git remote remove origin 2>nul
git remote add origin https://github.com/%U%/%2.git >> "%LOG%" 2>&1
git push -u origin main >> "%LOG%" 2>&1
exit /b
