@echo off
REM === Visor IFC — lanzador robusto (de despacho) ===
REM Sirve por HTTP (el worker de fragments no arranca desde file://) y abre el visor.
REM Si el servidor ya esta activo en el 8007, solo abre el navegador (no duplica).
cd /d "%~dp0"
set "URL=http://localhost:8007/visor-ifc-v1.0.html"

REM --- ¿hay ya un servidor escuchando en el 8007? ---
powershell -NoProfile -Command "try{ $c=New-Object Net.Sockets.TcpClient; $c.Connect('localhost',8007); $c.Close(); exit 0 } catch { exit 1 }" >nul 2>&1
if %errorlevel%==0 (
  echo Servidor ya activo en el 8007. Abriendo el visor...
  start "" "%URL%"
  goto :eof
)

echo Iniciando servidor en http://localhost:8007 ...
start "" "%URL%"

REM --- arranca el servidor en su propia ventana MINIMIZADA (sigue vivo aunque cambies de ventana) ---
where py >nul 2>nul && ( start "Visor IFC - servidor (no cerrar)" /min py -m http.server 8007 & goto :eof )
where python >nul 2>nul && ( start "Visor IFC - servidor (no cerrar)" /min python -m http.server 8007 & goto :eof )

echo No se encontro Python. Instala Python o usa otro servidor estatico en el puerto 8007.
pause
