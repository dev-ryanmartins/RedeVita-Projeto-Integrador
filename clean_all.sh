#!/bin/bash
# Script para remover todas as linhas de Co-authored-by e Generated with

echo "WARNING: This script rewrites Git history."
echo "Make sure you have backed up the repository."
echo ""

FILTER_BRANCH_SQUELCH_WARNING=1
git filter-branch -f --msg-filter '
    # Remover todas as linhas Co-authored-by
    sed -e "/^Co-authored-by/d" -e "/^Generated with/d"
' --tag-name-filter cat -- --all

rm -rf .git/refs/original/

echo "History rewritten successfully."
echo ""
echo "Now execute:"
echo "1. git push origin --force --all"
echo "2. git push origin --force --tags"
