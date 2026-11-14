@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"
title RedeVita - Apresentacao (servidor local)

echo ============================================================
echo    RedeVita - INICIAR APRESENTACAO (1 clique)
echo ============================================================
echo.

REM ---------- 1) Localizar e ativar a venv --------------------
set "VENV_DIR="
if exist ".venv\Scripts\activate.bat" set "VENV_DIR=.venv"
if not defined VENV_DIR if exist "venv\Scripts\activate.bat" set "VENV_DIR=venv"

if defined VENV_DIR (
    call "%VENV_DIR%\Scripts\activate.bat"
    set "PYTHON=%VENV_DIR%\Scripts\python.exe"
    echo [OK] Ambiente virtual ativado: %VENV_DIR%
) else (
    echo [AVISO] Nenhuma venv encontrada ^(.venv ou venv^).
    echo         Usando o Python do sistema. Rode configurar.bat para criar a venv.
    set "PYTHON=python"
)

REM ---------- 2) Conferir dependencias ------------------------
"%PYTHON%" -c "import flask, sqlalchemy, dotenv" >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Dependencias Python ausentes. Execute configurar.bat primeiro.
    pause
    exit /b 1
)
echo [OK] Dependencias verificadas.

REM ---------- 3) Arquivo .env seguro --------------------------
if not exist ".env" (
    if exist ".env.demo" (
        copy /Y ".env.demo" ".env" >nul
        echo [OK] .env criado a partir de .env.demo.
    ) else if exist ".env.example" (
        copy /Y ".env.example" ".env" >nul
        echo [OK] .env criado a partir de .env.example.
    )
)

REM Garante que SECRET_KEY esteja definida (gera uma na hora se faltar).
set "SECRET_OK="
if defined SECRET_KEY set "SECRET_OK=1"
if not defined SECRET_OK if exist ".env" findstr /B /C:"SECRET_KEY=" ".env" >nul 2>&1 && set "SECRET_OK=1"
if not defined SECRET_OK (
    for /f "usebackq delims=" %%s in (`"%PYTHON%" -c "import secrets;print(secrets.token_urlsafe(48))"`) do set "SECRET_KEY=%%s"
    echo [OK] SECRET_KEY gerada para esta sessao.
)

REM ---------- 4) Garantir o banco de demonstracao -------------
if not exist "instance\redevita_demo.db" (
    echo [INFO] Banco de demonstracao ausente. Gerando dados do seed...
    "%PYTHON%" seed_apresentacao.py
)

REM ---------- 5) Banner: URL + cola de credenciais ------------
echo.
echo ============================================================
echo    SERVIDOR LOCAL:  http://127.0.0.1:5000
echo ============================================================
echo.
echo    COLA DE CREDENCIAIS  (senha unica: RedeVita@2026)
echo    --------------------------------------------------------
echo     ADMIN        admin@redevita.demo
echo     FARMACIA     farmacia1@redevita.demo | farmacia2@redevita.demo
echo     MEDICO       medico1@redevita.demo   | medico2@redevita.demo
echo     PACIENTE     paciente1@redevita.demo | paciente2 / paciente3
echo     INSTITUICAO  instituicao1@redevita.demo | instituicao2@redevita.demo
echo    --------------------------------------------------------
echo    DICA: na tela de login clique em "Acesso rapido (demonstracao)"
echo          para entrar em 1 clique, sem digitar senha.
echo    Pressione CTRL+C para encerrar o servidor.
echo ============================================================
echo.

"%PYTHON%" rodar.py

echo.
echo Servidor encerrado.
pause
