@echo off
REM Sirve la carpeta del proyecto por HTTP y abre el visor PoC en el navegador.
REM Evita el problema de abrir como archivo local (file://), que bloquea el worker.
cd /d "%~dp0"
echo Iniciando servidor local en http://localhost:8000 ...
start "" "http://localhost:8000/visor-poc-thatopen.html"
python -m http.server 8000
