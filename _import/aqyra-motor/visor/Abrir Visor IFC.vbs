' Visor IFC — ejecuta el lanzador SIN ventana de consola
Dim fso, sh, here
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh = CreateObject("WScript.Shell")
here = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = here
' 0 = ventana oculta ; False = no esperar
sh.Run """" & here & "\Abrir Visor IFC.bat""", 0, False
