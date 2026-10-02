@echo off
echo ========================================
echo   🚀 ExamFlow - Iniciando Servidor
echo ========================================
echo.

echo 📂 Entrando na pasta...
cd /d "%~dp0"

echo 🚀 Iniciando servidor na porta 8001...
start "ExamFlow API" /min ".venv\Scripts\python.exe" -m uvicorn backend.main:app --host 0.0.0.0 --port 8001

echo ✅ Servidor iniciado!
echo 📌 Acesse localmente: http://127.0.0.1:8001
echo.
echo ⏳ Pressione qualquer tecla para fechar esta janela...
pause >nul
