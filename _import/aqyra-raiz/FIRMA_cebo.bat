@echo off
setlocal EnableExtensions
REM ============================================================
REM  FIRMA_cebo.bat  -  sella el cebo (capa de elementos + parking)
REM  Sello de dos llaves: Llave 1 = golden verde (ya verificada);
REM  Llave 2 = tu firma GPG sobre los tags. Lanzar con ENTER.
REM  Firma con tu clave GPG POR DEFECTO (la misma que firmo el
REM  manifiesto del motor: ed25519 8FD1E413...0942).
REM  (Opcional) para forzar otra clave, rellena SIGNKEY abajo.
REM ============================================================
set "SIGNKEY="
REM  ej: set "SIGNKEY=8FD1E413XXXXXXXX...0942"

cd /d "%~dp0..\Entorno"
set "LOG=%~dp0FIRMA_cebo_resultado.txt"
echo FIRMA cebo - %date% %time% > "%LOG%"
echo repo: %CD% >> "%LOG%"

REM --- 1. limpiar lock huerfano ---
if exist ".git\index.lock" del /f /q ".git\index.lock"

REM --- 2. elegir flag de firma (-s clave por defecto / -u clave forzada) ---
set "SIGNFLAG=-s"
if defined SIGNKEY set "SIGNFLAG=-u %SIGNKEY%"
echo signflag: %SIGNFLAG% >> "%LOG%"
echo ===== GPG secret keys ===== >> "%LOG%"
gpg --list-secret-keys >> "%LOG%" 2>&1

REM --- 3. staging explicito (solo lo que entra en la firma) ---
git add publico/demo/src/diseno.ts publico/demo/src/model.ts publico/demo/test/columns.golden.test.ts publico/demo/test/parking.golden.test.ts publico/demo/fixtures
REM  (VERIFICAR_V3_resultado.txt esta gitignorado; la ref de Llave 1 va en el tag)

REM --- 4. PUERTA DE SECRETOS ---
git diff --cached --name-only > "%TEMP%\cebo_staged.txt"
echo ===== STAGED ===== >> "%LOG%"
type "%TEMP%\cebo_staged.txt" >> "%LOG%"
findstr /I /R /C:"\.env" /C:"node_modules/" /C:"\.key" /C:"\.pem" /C:"secrets" "%TEMP%\cebo_staged.txt" >nul
if %errorlevel%==0 goto :secreto

REM --- 5. commit (si no hay cambios, sigue y etiqueta el HEAD actual) ---
git commit -m "Cebo: capa de elementos (IfcColumn/Slab+huecos/Wall/Door/Window/Stair) + parking; golden 35/35 + 7/7; typecheck limpio" >> "%LOG%" 2>&1

REM --- 6. tags firmados (te pedira la passphrase GPG) ---
git tag %SIGNFLAG% cebo-elementos-2026-06-28 -m "Cebo capa de elementos - columns.golden 35/35 - suite 144/144 - VERIFICAR 28/06 verde" >> "%LOG%" 2>&1
if errorlevel 1 goto :tagfail
git tag %SIGNFLAG% cebo-parking-2026-06-28 -m "Cebo parking en peine - parking.golden 7/7 - VERIFICAR 28/06 verde" >> "%LOG%" 2>&1
if errorlevel 1 goto :tagfail

REM --- 7. push rama + tags ---
git push origin main --follow-tags >> "%LOG%" 2>&1
if errorlevel 1 goto :pushfail

REM --- 8. verificar firmas ---
echo ===== VERIFY ===== >> "%LOG%"
git tag -v cebo-elementos-2026-06-28 >> "%LOG%" 2>&1
git tag -v cebo-parking-2026-06-28 >> "%LOG%" 2>&1
echo. >> "%LOG%"
echo OK: commit + 2 tags firmados + push completados. >> "%LOG%"
echo.
echo LISTO. Revisa FIRMA_cebo_resultado.txt
goto :fin

:secreto
echo SECRETO DETECTADO en el staging. Abortado SIN commit. >> "%LOG%"
git reset >> "%LOG%" 2>&1
echo SECRETO DETECTADO (.env u otro). Hice git reset y abort.
goto :fin

:tagfail
echo ERROR creando/firmando un tag. >> "%LOG%"
echo Causas tipicas: passphrase incorrecta; git no encuentra gpg; o el tag ya existe. >> "%LOG%"
echo Si git no encuentra tu gpg, configura una vez: >> "%LOG%"
echo   git config --global gpg.program "C:\Program Files\GnuPG\bin\gpg.exe" >> "%LOG%"
echo ERROR firmando tags. Revisa FIRMA_cebo_resultado.txt (al final hay una pista).
goto :fin

:pushfail
echo ERROR en push (credenciales/remoto). Commit y tags quedan en LOCAL. >> "%LOG%"
echo ERROR en push. El commit y los tags estan en local; revisa el log.
goto :fin

:fin
echo.
pause
