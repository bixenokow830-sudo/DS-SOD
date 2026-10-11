@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0init-backup.ps1" -ProjectDir "%~dp0" -Message "增量备份"
pause
