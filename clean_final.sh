#!/bin/bash
# Script final para limpar histórico Git de menções de bots de IA

echo "WARNING: This script rewrites Git history."
echo "Make sure you have backed up the repository."
echo ""

# Executar git filter-branch com sed correto
FILTER_BRANCH_SQUELCH_WARNING=1
git filter-branch -f --msg-filter '
    sed -e "/Co-authored-by/d" -e "/Generated with \[Devin\]/d"
' --tag-name-filter cat -- --all

# Limpar backup
rm -rf .git/refs/original/

echo "History rewritten successfully."
echo ""
echo "Now execute:"
echo "1. git push origin --force --all"
echo "2. git push origin --force --tags"
