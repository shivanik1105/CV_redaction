' Starts the CV Redaction server silently in the background (no window).
' Place this file in your Windows Startup folder, or run setup_autostart.bat.
Dim WshShell
Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\shiva\Downloads\samplecvs"
WshShell.Run """C:\Users\shiva\Downloads\samplecvs\resume\Scripts\python.exe"" ""C:\Users\shiva\Downloads\samplecvs\redact_server.py""", 0, False
Set WshShell = Nothing
