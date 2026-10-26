@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo   启动主页编辑器...
echo.
python tools\admin.py
if errorlevel 1 (
  echo.
  echo   启动失败：请确认已安装 Python 3 并在 PATH 中。
  pause
)
