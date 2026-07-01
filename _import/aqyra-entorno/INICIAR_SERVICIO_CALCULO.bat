@echo off
REM ============================================================
REM  Aqyra V3 - SERVICIO DE CALCULO local (anzuelo, D-019.C.4)
REM  Arranca el endpoint que el POST del post-proceso del visor
REM  llama (solve/qa/sign/ec3). Deja esta ventana ABIERTA.
REM  Productor PROVISIONAL: PyNite (numeros reales ya; la 2.a
REM  llave sera independiente al cablear motor-fem).
REM ============================================================
setlocal
cd /d "%~dp0"

set "PY=python"
where python >nul 2>nul || set "PY=py"
where %PY% >nul 2>nul
if errorlevel 1 (
  echo No se encuentra Python. Instala Python 3.10+ desde https://python.org y reintenta.
  pause
  exit /b 1
)

echo Instalando motor de calculo (PyNite + numpy) la primera vez...
%PY% -m pip install --quiet numpy PyNiteFEA

REM Los paquetes del pipeline no estan pip-instalados: se anclan por PYTHONPATH.
set "P=%~dp0privado"
set "PYTHONPATH=%P%\puente-calculo\src;%P%\qa-pynite\src;%P%\verificacion-ec\src;%P%\firma\src;%P%\servicio-calculo\src"

echo.
echo Arrancando servicio en http://127.0.0.1:8765   (Ctrl+C para parar)
echo   POST /solve  /qa  /sign  /ec3      GET /health
echo.
%PY% -m servicio_calculo
pause
