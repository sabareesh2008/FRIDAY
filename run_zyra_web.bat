@echo off
cd /d "%~dp0"
python web_main.py
if errorlevel 1 pause
