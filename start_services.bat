@echo off
color 0A
echo ========================================
echo    🤖 CHATBOT EDUCACIONAL
echo ========================================
echo.
echo Iniciando serviços...
echo.

REM Mata processos anteriores se existirem
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1

echo 🚀 Iniciando Backend...
start "Backend API" /MIN cmd /k "cd /d \"%~dp0\backend\" && python -m uvicorn main:app --host 127.0.0.1 --port 8000"

echo ⏳ Aguardando 5 segundos...
timeout /t 5 /nobreak >nul

echo 🌐 Iniciando Frontend...
start "Frontend React" cmd /k "cd /d \"%~dp0\" && npm run dev"

echo.
echo ✅ Serviços iniciados com sucesso!
echo.
echo 🌐 Frontend: http://localhost:3000/
echo 🖥️ Backend:  http://127.0.0.1:8000/
echo 📖 API Docs: http://127.0.0.1:8000/docs
echo.
echo Mantenha esta janela aberta para monitorar os serviços.
echo Pressione Ctrl+C para parar todos os serviços.
echo.
pause

