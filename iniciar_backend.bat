@echo off
color 0A
echo ========================================
echo     🔧 INICIANDO BACKEND
echo ========================================
echo.
cd /d "%~dp0\backend"
echo Diretório atual: %CD%
echo.
echo 🚀 Iniciando servidor FastAPI...
echo.
python -m uvicorn main:app --host 127.0.0.1 --port 8000
echo.
echo ❌ Backend foi encerrado.
pause

