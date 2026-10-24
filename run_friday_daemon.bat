@echo off
cd /d "%~dp0"
start "" pythonw daemon_main.py
if errorlevel 1 start "" python daemon_main.py
