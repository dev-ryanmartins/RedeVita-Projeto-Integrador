@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"
title RedeVita - Resetar DEMO (seed do zero)

echo ============================================================
echo    RedeVita - RESETAR DEMO  (rodar ~15 min antes)
echo ============================================================
echo    ATENCAO: isto APAGA o banco de demonstracao e repopula
echo             todos os dados do seed do zero.
echo.
echo    Pressione CTRL+C para cancelar. Iniciando em 5 segundos...
timeout /t 5 >nul

REM ---------- 1) Localizar e ativar a venv --------------------
set "VENV_DIR="
if exist ".venv\Scripts\activate.bat" set "VENV_DIR=.venv"
if not defined VENV_DIR if exist "venv\Scripts\activate.bat" set "VENV_DIR=venv"

if defined VENV_DIR (
    call "%VENV_DIR%\Scripts\activate.bat"
    set "PYTHON=%VENV_DIR%\Scripts\python.exe"
    echo [OK] Ambiente virtual ativado: %VENV_DIR%
) else (
    echo [AVISO] Nenhuma venv encontrada ^(.venv ou venv^). Usando Python do sistema.
    set "PYTHON=python"
)

REM ---------- 2) Arquivo .env seguro --------------------------
if not exist ".env" (
    if exist ".env.demo" (
        copy /Y ".env.demo" ".env" >nul
        echo [OK] .env criado a partir de .env.demo.
    ) else if exist ".env.example" (
        copy /Y ".env.example" ".env" >nul
        echo [OK] .env criado a partir de .env.example.
    )
)

set "SECRET_OK="
if defined SECRET_KEY set "SECRET_OK=1"
if not defined SECRET_OK if exist ".env" findstr /B /C:"SECRET_KEY=" ".env" >nul 2>&1 && set "SECRET_OK=1"
if not defined SECRET_OK (
    for /f "usebackq delims=" %%s in (`"%PYTHON%" -c "import secrets;print(secrets.token_urlsafe(48))"`) do set "SECRET_KEY=%%s"
    echo [OK] SECRET_KEY gerada para esta sessao.
)

REM ---------- 3) Resetar e repopular do zero ------------------
echo.
echo [1/1] Recriando o banco e aplicando o seed de apresentacao...
echo.
"%PYTHON%" seed_apresentacao.py --reset
if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao resetar a demonstracao. Verifique as mensagens acima.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo    DEMO PRONTA!  URL: http://127.0.0.1:5000
echo    Suba o servidor com: iniciar_apresentacao.bat
echo    Senha unica de todos os perfis: RedeVita@2026
echo ============================================================
echo.
pause
