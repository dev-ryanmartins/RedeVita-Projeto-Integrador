#!/bin/bash
echo ""
echo "===================================================="
echo "  RedeVita — Iniciando servidor local"
echo "===================================================="
echo ""

if [ ! -d ".venv" ]; then
    echo "[ERRO] Ambiente virtual nao encontrado."
    echo "Execute primeiro: bash configurar.sh"
    exit 1
fi

if [ ! -f ".env" ]; then
    echo "[AVISO] Arquivo .env nao encontrado."
    echo "O sistema usara SQLite como banco de dados."
    echo ""
fi

source .venv/bin/activate

echo "Iniciando Flask em http://127.0.0.1:5000"
echo "Pressione CTRL+C para encerrar."
echo ""

cd backend
python main.py
