' Visor IFC (app de escritorio) — abre Electron directamente, SIN consola.
' Usa el Electron ya instalado en node_modules (no necesita construir un .exe).
Dim fso, sh, here, exe, mainjs
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh  = CreateObject("WScript.Shell")
here   = fso.GetParentFolderName(WScript.ScriptFullName)
exe    = here & "\node_modules\electron\dist\electron.exe"
mainjs = here & "\main.js"
sh.CurrentDirectory = here
If fso.FileExists(exe) Then
  ' 0 = ventana oculta ; False = no esperar
  sh.Run """" & exe & """ """ & mainjs & """", 0, False
Else
  ' Electron aun no instalado: instalar y arrancar (consola visible solo la 1a vez)
  sh.Run "cmd /c cd /d """ & here & """ && npm install && npm start", 1, False
End If
