@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0sync-artifacts-once.ps1"
pause
