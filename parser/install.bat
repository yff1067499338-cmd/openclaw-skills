@echo off
chcp 65001 >nul
echo ════════════════════════════════════════
echo   微信公众号文章采集 - 环境安装
echo ════════════════════════════════════════
echo.

echo 正在安装 Python 依赖...
pip install selenium requests beautifulsoup4

echo.

echo ════════════════════════════════════════
echo   安装完成！运行方式：
echo   python wechat_to_obsidian.py
echo ════════════════════════════════════════
echo.
pause
