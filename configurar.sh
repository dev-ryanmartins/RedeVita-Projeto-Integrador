#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "===================================================="
echo "  RedeVita — Configuração do Ambiente Local"
echo "===================================================="
echo ""

PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    echo "[ERRO] Python 3.11+ não encontrado."
    echo "Instale o Python e execute novamente este script."
    exit 1
fi

if [ ! -x ".venv/bin/python" ]; then
    echo "[1/3] Criando ambiente virtual..."
    "$PYTHON_BIN" -m venv .venv
else
    echo "[1/3] Ambiente virtual já existe."
fi

PYTHON=".venv/bin/python"
echo "[2/3] Instalando dependências..."
"$PYTHON" -m pip install --upgrade pip
"$PYTHON" -m pip install -r backend/requirements.txt

if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    cp ".env.example" ".env"
    echo "[3/3] Arquivo .env criado a partir de .env.example."
else
    echo "[3/3] Arquivo .env já configurado ou dispensável."
fi

echo ""
echo "Configuração concluída. Execute: ./iniciar.sh"