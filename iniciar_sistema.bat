@echo off
color 0A
echo ========================================
echo    🤖 CHATBOT EDUCACIONAL
echo ========================================
echo.
echo 🚀 Iniciando sistema...
echo.

REM Limpar processos anteriores
echo 🧹 Limpando processos anteriores...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
timeout /t 2 /nobreak >nul

REM Iniciar backend (versão simplificada e estável)
echo 🖥️ Iniciando Backend API...
start "Backend API" /MIN powershell -Command "cd '%~dp0\backend'; Start-Process python -ArgumentList '-m', 'uvicorn', 'main_simple_fixed:app', '--host', '127.0.0.1', '--port', '8000' -WindowStyle Hidden"

REM Aguardar backend inicializar
echo ⏳ Aguardando backend inicializar...
timeout /t 8 /nobreak >nul

REM Verificar se backend está rodando
netstat -an | findstr :8000 >nul
if errorlevel 1 (
    echo ❌ Backend não conseguiu iniciar
    pause
    exit /b 1
) else (
    echo ✅ Backend iniciado com sucesso!
)

REM Iniciar frontend
echo 🌐 Iniciando Frontend React...
start "Frontend React" cmd /k "cd /d '%~dp0' && npm run dev"

echo.
echo ✅ Sistema iniciado com sucesso!
echo.
echo 🌍 URLs de Acesso:
echo 🌐 Frontend: http://localhost:3000/
echo 🖥️ Backend:  http://127.0.0.1:8000/
echo 📖 API Docs: http://127.0.0.1:8000/docs
echo 🆗 Health:   http://127.0.0.1:8000/health
echo.
echo 📄 O backend está rodando em modo simplificado.
echo 🗒️ Para funcionalidades de IA, configure OpenAI no .env
echo.
echo 📌 Mantenha os terminais abertos para manter os serviços ativos.
echo Pressione qualquer tecla para abrir o navegador...
pause >nul

REM Abrir navegador
start http://localhost:3000/

