@echo off
REM ============================================================
REM  Aqyra V3 - tests del SERVICIO DE CALCULO (12 casos)
REM  Maquina de las dos llaves + EC3 + guarda de firma + HTTP.
REM  NO requiere PyNite (usa productor/solver falsos).
REM  Resultado en VERIFICAR_SERVICIO_resultado.txt
REM ============================================================
setlocal
cd /d "%~dp0"
set LOG=VERIFICAR_SERVICIO_resultado.txt
echo Aqyra V3 - tests servicio-calculo > "%LOG%"
echo Fecha: %date% %time% >> "%LOG%"
echo. >> "%LOG%"

set "PY=python"
where python >nul 2>nul || set "PY=py"

%PY% privado\servicio-calculo\tests\test_service.py >> "%LOG%" 2>&1

echo. >> "%LOG%"
echo ===== FIN ===== >> "%LOG%"
echo Listo. Resultado en: VERIFICAR_SERVICIO_resultado.txt  (busca "OK" y "Ran 12 tests")
pause
