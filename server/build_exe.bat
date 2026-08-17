@echo off
chcp 65001 >nul
rem ============================================================
rem  打包桌面版 NavApp.exe（双击运行或命令行执行均可）
rem  产物: dist\NavApp.exe
rem ============================================================
cd /d "%~dp0"

rem 安装桌面版专用依赖；已安装则自动跳过
".venv\Scripts\python.exe" -m pip install PyInstaller
".venv\Scripts\python.exe" -m pip install -q -r requirements-desktop.txt
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --onefile --windowed --name NavApp --icon "../web/public/favicon.ico" --add-data "../web/dist;web/dist" desktop_launcher.py

if errorlevel 1 (
    echo.
    echo [build] 构建失败，请查看上方错误信息。
) else (
    echo.
    echo [build] 构建成功: %cd%\dist\NavApp.exe
)
pause
rem ============================================================
rem  打包桌面版 NavApp.exe（双击运行或命令行执行均可）
rem  产物: dist\NavApp.exe
rem ============================================================
cd /d "%~dp0"

rem 安装桌面版专用依赖；已安装则自动跳过
".venv\Scripts\python.exe" -m pip install -q -r requirements-desktop.txt

".venv\Scripts\python.exe" -m PyInstaller --noconfirm --onefile --windowed --name NavApp --icon "../web/public/favicon.ico" --add-data "../web/dist;web/dist" desktop_launcher.py

if errorlevel 1 (
    echo.
    echo [build] 构建失败，请查看上方错误信息。
) else (
    echo.
    echo [build] 构建成功: %cd%\dist\NavApp.exe
)
pause
