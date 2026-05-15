@echo off
chcp 65001 >nul
echo.
echo ====================================================
echo   RedeVita — Iniciando servidor local
echo ====================================================
echo.

if not exist ".venv\" (
    echo [ERRO] Ambiente virtual nao encontrado.
    echo Execute primeiro: configurar.bat
    pause
    exit /b 1
)

if not exist ".env" (
    echo [AVISO] Arquivo .env nao encontrado.
    echo O sistema usara SQLite como banco de dados.
    echo Para usar MySQL, crie o .env com DATABASE_URL.
    echo.
)

call .venv\Scripts\activate.bat

echo Iniciando Flask em http://127.0.0.1:5000
echo Pressione CTRL+C para encerrar.
echo.

cd backend
python main.py
