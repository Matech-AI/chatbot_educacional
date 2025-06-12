@echo off
echo ========================================
echo    🤖 CHATBOT EDUCACIONAL
echo ========================================
echo.
echo Iniciando o projeto...
echo.
echo 1. Abrindo terminal para BACKEND...
start cmd /k "cd /d %~dp0backend && python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload"
echo.
echo 2. Aguardando 3 segundos...
timeout /t 3 /nobreak >nul
echo.
echo 3. Abrindo terminal para FRONTEND...
start cmd /k "cd /d %~dp0 && npm run dev"
echo.
echo ✅ Ambos os serviços foram iniciados!
echo.
echo 📱 Frontend: http://localhost:3000/
echo 🔧 Backend:  http://127.0.0.1:8000/
echo 📚 API Docs: http://127.0.0.1:8000/docs
echo.
echo Pressione qualquer tecla para fechar esta janela...
pause >nul

