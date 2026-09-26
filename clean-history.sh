#!/bin/bash
# Script para limpar histórico Git de menções de bots de IA
# Uso: ./clean-history.sh

echo "⚠️  AVISO: Este script reescreve o histórico Git."
echo "Certifique-se de ter feito backup do repositório."
echo ""
read -p "Deseja continuar? (s/n): " confirm

if [ "$confirm" != "s" ] && [ "$confirm" != "S" ]; then
    echo "Operação cancelada."
    exit 0
fi

echo "Iniciando limpeza do histórico..."

# Reescrever histórico removendo linhas indesejadas
git filter-branch --force --env-filter '
    # Remover linhas de Co-authored-by
    sed -i "/Co-authored-by/d" "$GIT_COMMIT_MESSAGE_FILE"
    
    # Remover linha "Generated with [Devin]"
    sed -i "/Generated with \[Devin\]/d" "$GIT_COMMIT_MESSAGE_FILE"
    
    # Remover linhas vazias adicionais após remoção
    sed -i "/^$/d" "$GIT_COMMIT_MESSAGE_FILE"
' --tag-name-filter cat -- --all

echo "✅ Histórico reescrito com sucesso."
echo ""
echo "Agora execute:"
echo "1. git push origin --force --all"
echo "2. git push origin --force --tags"
echo ""
echo "AVISO: Todos os colaboradores precisarão clonar novamente o repositório."
