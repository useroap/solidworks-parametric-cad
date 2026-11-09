' run_silent.vbs — Lanzador 100% invisible para tareas interactivas en Windows
' Parametric CAD Automation Engine
' Ejecuta cualquier comando o archivo por lotes con ventana totalmente oculta (SW_HIDE = 0)
' sin parpadeo de consola ni ventanas negras en el escritorio del usuario.

If WScript.Arguments.Count < 1 Then
    WScript.Quit 1
End If

Set WshShell = CreateObject("WScript.Shell")
intReturn = WshShell.Run("cmd.exe /c """ & WScript.Arguments(0) & """", 0, True)
WScript.Quit intReturn
