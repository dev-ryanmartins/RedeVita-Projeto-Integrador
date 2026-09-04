#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "===================================================="
echo "  RedeVita — Inicialização e Verificação"
echo "===================================================="
echo ""

if [ ! -x ".venv/bin/python" ]; then
    echo "[ERRO] Ambiente virtual nao encontrado."
    echo "Execute primeiro: bash configurar.sh"
    exit 1
fi

PYTHON=".venv/bin/python"

echo "[1/2] Verificando dependencias Python..."
if ! "$PYTHON" -c "import flask, sqlalchemy, dotenv" 2>/dev/null; then
    echo "[ERRO] Dependencias Python nao instaladas."
    echo "Execute: bash configurar.sh"
    exit 1
fi
echo "[OK] Dependencias verificadas."
echo ""

echo "[2/2] Iniciando servidor Flask..."
echo "A aplicacao estara disponivel em: http://127.0.0.1:5000"
echo "Pressione CTRL+C para encerrar."
echo ""

exec "$PYTHON" rodar.py
