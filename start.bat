@echo off
setlocal
set "ROOT=%~dp0"

rem 如使用项目内虚拟环境，可取消下一行注释
rem set "PYTHON=%ROOT%venv\Scripts\python.exe"
if not defined PYTHON set "PYTHON=python"

start "Rongcheng Backend" cmd /k "cd /d ""%ROOT%python"" && ""%PYTHON%"" app.py"
timeout /t 5 /nobreak >nul
start "Rongcheng Frontend" cmd /k "cd /d ""%ROOT%frontend"" && npm run dev"

echo Backend:  http://localhost:5000
echo Frontend: http://localhost:3000
pause >nul
