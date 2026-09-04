@echo off
chcp 65001 >nul
echo.
echo ====================================================
echo   RedeVita — Configuracao do Ambiente Local
echo ====================================================
echo.

REM Verificar se Python esta instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado. Instale Python 3.11+ em https://python.org
    pause
    exit /b 1
)

echo [OK] Python encontrado.

REM Criar ambiente virtual se nao existir ou estiver incompleto
if not exist ".venv\Scripts\python.exe" (
    echo Criando ambiente virtual...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERRO] Nao foi possivel criar o ambiente virtual.
        pause
        exit /b 1
    )
    echo [OK] Ambiente virtual criado.
) else (
    echo [OK] Ambiente virtual ja existe.
)

REM Instalar dependencias usando o interpretador da virtualenv
echo Instalando dependencias...
set "PYTHON=.venv\Scripts\python.exe"
"%PYTHON%" -m pip install --upgrade pip -q
if errorlevel 1 (
    echo [ERRO] Falha ao atualizar o pip.
    pause
    exit /b 1
)
"%PYTHON%" -m pip install -r backend\requirements.txt -q
if errorlevel 1 (
    echo [ERRO] Falha ao instalar as dependencias.
    pause
    exit /b 1
)
echo [OK] Dependencias instaladas.

REM Criar .env se nao existir, sem substituir configuracoes existentes
if not exist ".env" (
    if exist ".env.example" (
        copy /Y ".env.example" ".env" >nul
        echo [OK] Arquivo .env criado a partir de .env.example.
    ) else (
        echo [AVISO] .env.example nao encontrado; serao usados os padroes locais.
    )
) else (
    echo [OK] Arquivo .env encontrado.
)

echo.
echo ====================================================
echo   Configuracao concluida!
echo   Execute: iniciar.bat
echo ====================================================
echo.
pause
