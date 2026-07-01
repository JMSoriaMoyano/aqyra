@echo off
REM ============================================================
REM  Aqyra - Fase 1: COMMIT + SUBIR el MOTOR
REM  Estructurando  ->  github.com/JMSoriaMoyano/aqyra-motor (PRIVADO)
REM  REQUISITO: el repo aqyra-motor ya existe vacio (Private, sin README).
REM  Doble clic. La primera subida abrira el navegador para tu login.
REM  Resultado en: ..\FASE1_git_resultado_MOTOR.txt
REM ============================================================
setlocal
set "U=JMSoriaMoyano"
set "LOG=%~dp0..\FASE1_git_resultado_MOTOR.txt"
cd /d "%~dp0..\Estructurando"

echo Aqyra Fase 1 push MOTOR - %date% %time% > "%LOG%"

REM 1) Limpiar lock huerfano y ficheros temporales de prueba
if exist ".git\index.lock" del /f /q ".git\index.lock"
if exist ".__write_test" del /f /q ".__write_test"
if exist "%~dp0.__write_test" del /f /q "%~dp0.__write_test"

REM 2) Commit de los cambios pendientes (CN-3 + convenciones + Olas 4-6)
git add -A >> "%LOG%" 2>&1
git commit -m "Fase 1 (motor): reconciliacion CN-3 + convenciones CN-1/2/3; actualizacion Olas 4-6 y roadmaps visor v0.5-v1.1" >> "%LOG%" 2>&1

REM 3) Rama main + remote privado
git branch -M main >> "%LOG%" 2>&1
git remote remove origin 2>nul
git remote add origin https://github.com/%U%/aqyra-motor.git >> "%LOG%" 2>&1

REM 4) Subir
git push -u origin main >> "%LOG%" 2>&1

echo ===== FIN ===== >> "%LOG%"
echo.
echo Listo. aqyra-motor subido (privado). Revisa FASE1_git_resultado_MOTOR.txt
pause
