@echo off
REM Instala (una sola vez) las dependencias del pipeline IFC->fragments.
REM Requiere Node.js instalado (https://nodejs.org). Necesita internet.
cd /d "%~dp0"
echo Instalando @thatopen/fragments, three y web-ifc ...
call npm install --no-audit --no-fund
echo.
echo Hecho. Ya puedes convertir IFCs con:  convertir_ifc.bat  ruta\al\modelo.ifc
pause
