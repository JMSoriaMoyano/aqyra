@echo off
REM ============================================================
REM  Aqyra V3 - verificacion (typecheck + tests)
REM  Doble clic. Al terminar, deja el resultado en VERIFICAR_V3_resultado.txt
REM ============================================================
setlocal
cd /d "%~dp0publico"
set LOG=..\VERIFICAR_V3_resultado.txt
echo Aqyra V3 - verificacion > "%LOG%"
echo Fecha: %date% %time% >> "%LOG%"
echo. >> "%LOG%"

echo Instalando dependencias (puede tardar la primera vez)...
where pnpm >nul 2>nul
if %errorlevel%==0 (
  call pnpm install        >> "%LOG%" 2>&1
  echo. >> "%LOG%"
  echo ===== TYPECHECK ===== >> "%LOG%"
  call pnpm typecheck       >> "%LOG%" 2>&1
  echo. >> "%LOG%"
  echo ===== TESTS ===== >> "%LOG%"
  call pnpm test            >> "%LOG%" 2>&1
) else (
  echo pnpm no encontrado; usando npm/npx... >> "%LOG%"
  call npm install          >> "%LOG%" 2>&1
  echo. >> "%LOG%"
  echo ===== TYPECHECK ===== >> "%LOG%"
  call npx tsc -p tsconfig.check.json >> "%LOG%" 2>&1
  echo. >> "%LOG%"
  echo ===== TESTS ===== >> "%LOG%"
  call npx vitest run       >> "%LOG%" 2>&1
)

echo. >> "%LOG%"
echo ===== FIN ===== >> "%LOG%"
echo.
echo Listo. El resultado esta en:  VERIFICAR_V3_resultado.txt
echo (Abrelo y, si quieres, pegamelo aqui y lo reviso.)
echo.
pause
