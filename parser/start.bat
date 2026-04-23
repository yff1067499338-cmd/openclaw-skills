@echo off
cd /d "%~dp0"
python wechat_to_obsidian.py
echo.
echo ========================================
echo   Script finished. Press any key to close.
echo ========================================
pause >nul
