@echo off
REM ============================================================
REM  Aqyra V3 - cálculo real (dos llaves: QA PyNite + EC3 + firma)
REM  Doble clic. Resultado en VERIFICAR_CALCULO_resultado.txt
REM ============================================================
setlocal
cd /d "%~dp0"
set LOG=VERIFICAR_CALCULO_resultado.txt
echo Aqyra V3 - calculo real (dos llaves) > "%LOG%"
echo Fecha: %date% %time% >> "%LOG%"
echo. >> "%LOG%"

REM localizar Python
set "PY=python"
where python >nul 2>nul || set "PY=py"
where %PY% >nul 2>nul
if errorlevel 1 (
  echo No se encuentra Python. Instala Python 3.10+ desde https://python.org y reintenta. >> "%LOG%"
  echo No se encuentra Python. Instala Python 3.10+ desde https://python.org y reintenta.
  pause
  exit /b 1
)

echo Instalando motor de calculo (PyNite + numpy) la primera vez...
%PY% -m pip install --quiet numpy PyNiteFEA >> "%LOG%" 2>&1

echo ===== QA con PyNite (fisica D-018: gravedad -Z, reaccion +Z, N>0 traccion) ===== >> "%LOG%"
%PY% privado\qa-pynite\tests\test_qa.py >> "%LOG%" 2>&1
echo. >> "%LOG%"
echo ===== Aprovechamiento EC3 (que no cumple) ===== >> "%LOG%"
%PY% privado\verificacion-ec\tests\test_ec3.py >> "%LOG%" 2>&1
echo. >> "%LOG%"
echo ===== Pipeline completo: computed -^> qa-passed -^> verified-signed ===== >> "%LOG%"
%PY% privado\firma\tests\test_pipeline.py >> "%LOG%" 2>&1
echo. >> "%LOG%"
echo ===== FIN ===== >> "%LOG%"

echo.
echo Listo. Resultado en:  VERIFICAR_CALCULO_resultado.txt
echo Busca lineas "OK" y "X/X OK". Pegamelo aqui si quieres que lo revise.
echo.
pause
