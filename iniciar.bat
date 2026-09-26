@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo ====================================================
echo   RedeVita — Inicializacao e Verificacao
echo ====================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [ERRO] Ambiente virtual nao encontrado.
    echo Execute primeiro: configurar.bat
    pause
    exit /b 1
)

set "PYTHON=.venv\Scripts\python.exe"

echo [1/2] Verificando dependencias Python...
"%PYTHON%" -c "import flask, sqlalchemy, dotenv" >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Dependencias Python nao instaladas.
    echo Execute: configurar.bat
    pause
    exit /b 1
)
echo [OK] Dependencias verificadas.
echo.

echo [2/2] Iniciando servidor Flask...
echo A aplicacao estara disponivel em: http://127.0.0.1:5000
echo Pressione CTRL+C para encerrar.
echo.

"%PYTHON%" rodar.py
