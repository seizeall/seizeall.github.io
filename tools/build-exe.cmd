@echo off
chcp 65001 >nul
cd /d "%~dp0.."
echo.
echo   打包 HomepageEditor.exe ...
echo.
python -m PyInstaller --noconfirm --clean --onefile --noconsole ^
  --name HomepageEditor ^
  --icon "%CD%\assets\icon.ico" ^
  --hidden-import build ^
  --add-data "%CD%\tools\admin.html;tools" ^
  --add-data "%CD%\templates\index.template.html;templates" ^
  --distpath "%CD%" --workpath "%CD%\build" --specpath "%CD%\build" ^
  "%CD%\tools\admin.py"

if errorlevel 1 (
  echo.
  echo   打包失败：先运行  python -m pip install pyinstaller
  pause
  exit /b 1
)

if exist "%CD%\build" rmdir /s /q "%CD%\build"
echo.
echo   完成：%CD%\HomepageEditor.exe
echo.
pause
