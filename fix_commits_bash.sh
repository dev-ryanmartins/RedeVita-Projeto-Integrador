#!/bin/bash
# Script para limpar commits individualmente

echo "Iniciando limpeza de commits..."

# Obter commits que precisam de limpeza
COMMITS=$(git log --all --pretty=format:"%H" --grep="Devin\|bot")

if [ -z "$COMMITS" ]; then
    echo "Nenhum commit com menções de bot encontrado."
    exit 0
fi

echo "Encontrados commits para limpar."

# Para cada commit, editar a mensagem
for commit in $COMMITS; do
    echo "Processando commit: $commit"
    
    # Obter mensagem atual
    MSG=$(git show -s --format=%B $commit)
    
    # Limpar mensagem
    CLEANED_MSG=$(echo "$MSG" | sed -e "/^Co-authored-by/d" -e "/^Generated with/d" -e "/^$/N" -e "/^\\n$/D")
    
    # Reescrever commit
    git checkout $commit
    git commit --amend -m "$CLEANED_MSG"
done

# Voltar para o branch original
git checkout main

echo "Commits limpos com sucesso."
echo "Execute: git push origin --force --all"
