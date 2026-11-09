# Bridging Windows Desktop Isolation (`exebox` vs Interactive Session 1 ROT)

## 1. Problem Description (`MK_E_UNAVAILABLE`)

When an AI agent executes a shell command via `run_command` on Windows, the command often runs inside a restricted sandbox desktop (e.g., `WinSta0\exebox-...`).

In Windows COM architecture, the **Running Object Table (ROT)** is scoped per desktop/session security boundary:
- **SolidWorks 2025 (`SLDWORKS.exe`)** runs on the user's interactive desktop (`WinSta0\Default`, Session 1) and registers its `SldWorks.Application` moniker in the interactive ROT.
- A Python process launched directly inside `exebox` queries the sandboxed ROT, which is empty, and fails with:
  ```text
  pywintypes.com_error: (-2147221021, 'Operación no disponible', None, None)  # MK_E_UNAVAILABLE
  ```
- Furthermore, attempting to call `win32com.client.Dispatch("SldWorks.Application")` from `exebox` would launch a **second, invisible `SLDWORKS.exe` process** inside the sandbox desktop, violating `AGENTS.md` and exhausting system RAM/GDI handles.

---

## 2. Solution: Interactive Windows Scheduled Task Bridge

To execute `build_sw.py` inside the exact interactive desktop where SolidWorks 2025 is running:

1. Create a lightweight batch launcher `run_build.bat` in the CAD project folder (`tools/cad/<part_name>/run_build.bat`):
   ```bat
   @echo off
   cd /d "%~dp0"
   if not exist out mkdir out
   set TARGET=build_sw.py
   if exist out\run_target.txt set /p TARGET=<out\run_target.txt
   "C:\Users\USER\AppData\Local\Programs\Python\Python312\python.exe" -u %TARGET% > out\build_log.txt 2>&1
   echo EXIT=%ERRORLEVEL%>> out\build_log.txt
   ```
2. Register and trigger an On-Demand Windows Scheduled Task with `-LogonType Interactive` using `.agents/skills/solidworks-parametric-cad/scripts/run_in_interactive_session.ps1`:
   ```powershell
   powershell -ExecutionPolicy Bypass -File ".agents/skills/solidworks-parametric-cad/scripts/run_in_interactive_session.ps1" -WorkDir "tools\cad\my_part_project"
   ```
3. The task runs under the interactive user token on `WinSta0\Default`, connects immediately to the open SolidWorks 2025 window via `GetActiveObject("SldWorks.Application")`, writes real-time logs to `out\build_log.txt`, and appends `EXIT=0` upon completion.
4. **Zero Console Popups:** The task invokes `wscript.exe` (subsystem GUI) with [run_silent.vbs](../scripts/run_silent.vbs) using `SW_HIDE = 0`, ensuring that no black CMD console windows ever appear or flash on the user's desktop.
