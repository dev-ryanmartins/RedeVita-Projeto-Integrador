#!/bin/bash
# Script simples para limpar histórico Git de menções de bots de IA
# Usa git filter-branch (mais lento, mas já vem com Git)

echo "⚠️  AVISO: Este script reescreve o histórico Git."
echo "Certifique-se de ter feito backup do repositório."
echo ""
read -p "Deseja continuar? (s/n): " confirm

if [ "$confirm" != "s" ] && [ "$confirm" != "S" ]; then
    echo "Operação cancelada."
    exit 0
fi

echo "Iniciando limpeza do histórico..."

# Criar script de callback
cat > /tmp/clean_msg.sh << 'EOF'
#!/bin/bash
# Limpa mensagem de commit
sed -i \
  -e '/Co-authored-by.*bot/d' \
  -e '/Generated with \[Devin\]/d' \
  -e '/^$/N' \
  -e '/^\n$/D' \
  "$1"
EOF

chmod +x /tmp/clean_msg.sh

# Reescrever histórico
git filter-branch -f --msg-filter '/tmp/clean_msg.sh' --tag-name-filter cat -- --all

# Limpar backup
rm -rf .git/refs/original/

echo "✅ Histórico reescrito com sucesso."
echo ""
echo "Agora execute:"
echo "1. git push origin --force --all"
echo "2. git push origin --force --tags"
echo ""
echo "AVISO: Todos os colaboradores precisarão clonar novamente o repositório."
