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

REM Criar ambiente virtual se nao existir
if not exist ".venv\" (
    echo Criando ambiente virtual...
    python -m venv .venv
    echo [OK] Ambiente virtual criado.
) else (
    echo [OK] Ambiente virtual ja existe.
)

REM Ativar ambiente virtual e instalar dependencias
echo Instalando dependencias...
call .venv\Scripts\activate.bat
pip install --upgrade pip -q
pip install -r backend\requirements.txt -q
echo [OK] Dependencias instaladas.

REM Criar .env se nao existir
if not exist ".env" (
    echo.
    echo [ATENCAO] Arquivo .env nao encontrado.
    echo Crie o arquivo .env na raiz do projeto com o conteudo abaixo:
    echo.
    echo   SECRET_KEY=redevita_projeto_ads_2026
    echo   DATABASE_URL=mysql://root:Branco015@127.0.0.1:3306/redevita
    echo.
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
