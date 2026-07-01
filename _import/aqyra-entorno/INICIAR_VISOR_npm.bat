@echo off
title Aqyra - visor (npm)
cd /d "%~dp0publico\demo"
echo [Aqyra] Arrancando el visor en http://localhost:5173/calculista.html
echo [Aqyra] No cierres esta ventana mientras uses el visor.
call npm run dev
pause
