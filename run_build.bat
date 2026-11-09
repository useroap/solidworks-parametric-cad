@echo off
cd /d "%~dp0"
if not exist out mkdir out
set TARGET=build_sw.py
if exist out\run_target.txt set /p TARGET=<out\run_target.txt
"C:\Users\USER\AppData\Local\Programs\Python\Python312\python.exe" -u %TARGET% > out\build_log.txt 2>&1
(echo EXIT=%ERRORLEVEL%) >> out\build_log.txt
