@echo off
REM Re-sellado de Aqyra (cebo): typecheck + tests. Vuelca la salida a un fichero
REM que la IA puede leer de forma fiable. Doble clic o lanzar con Win+R.
cd /d "C:\Users\jmsor\Documents\Claude\Projects\Entorno\publico"
set "OUT=..\resellado_resultado.txt"
echo ===== RE-SELLADO Aqyra ===== > "%OUT%"
echo Fecha: %DATE% %TIME% >> "%OUT%"
echo. >> "%OUT%"
echo === TYPECHECK (npm run typecheck) === >> "%OUT%"
call npm run typecheck >> "%OUT%" 2>&1
echo TYPECHECK_EXIT=%ERRORLEVEL% >> "%OUT%"
echo. >> "%OUT%"
echo === TESTS (npm test) === >> "%OUT%"
call npm test >> "%OUT%" 2>&1
echo TEST_EXIT=%ERRORLEVEL% >> "%OUT%"
echo. >> "%OUT%"
echo ===== FIN ===== >> "%OUT%"
type "%OUT%"
echo.
echo (Resultado guardado en resellado_resultado.txt)
pause
