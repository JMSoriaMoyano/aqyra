@echo off
REM === Crea el icono "Visor IFC" en el Escritorio Y en esta carpeta (ejecutar UNA vez) ===
cd /d "%~dp0"
set "TARGET=%~dp0Abrir Visor IFC.vbs"
set "ICON=%~dp0icons\visor.ico"
set "HERE=%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ws=New-Object -ComObject WScript.Shell; $dests=@([Environment]::GetFolderPath('Desktop'), '%HERE%'.TrimEnd('\')); foreach($d in $dests){ $p=Join-Path $d 'Visor IFC.lnk'; $l=$ws.CreateShortcut($p); $l.TargetPath='%TARGET%'; $l.WorkingDirectory='%HERE%'; $l.IconLocation='%ICON%'; $l.Description='Abrir el Visor IFC'; $l.Save(); if(Test-Path $p){ Write-Host (' OK -> ' + $p) } else { Write-Host (' ERROR -> ' + $p) } }"
echo.
echo  Tienes el icono "Visor IFC" en el Escritorio y en esta carpeta (visor).
echo  Doble clic en cualquiera de los dos abre el visor.
echo.
pause
