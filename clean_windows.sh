#!/bin/bash
# Script para limpar histórico Git de menções de bots de IA
# Execute no Git Bash do Windows

echo "⚠️  AVISO: Este script reescreve o histórico Git."
echo "Certifique-se de ter feito backup do repositório."
echo ""
read -p "Deseja continuar? (s/n): " confirm

if [ "$confirm" != "s" ] && [ "$confirm" != "S" ]; then
    echo "Operação cancelada."
    exit 0
fi

echo "Iniciando limpeza do histórico..."

# Criar script de limpeza
cat > /tmp/clean_msg << 'EOF'
#!/bin/bash
python3 -c "
import sys
msg = sys.stdin.read()
lines = msg.split('\n')
cleaned = []
for line in lines:
    if 'Co-authored-by' in line and 'bot' in line.lower():
        continue
    if 'Generated with [Devin]' in line:
        continue
    if line.strip() == '' and cleaned and cleaned[-1].strip() == '':
        continue
    cleaned.append(line)
while cleaned and cleaned[-1].strip() == '':
    cleaned.pop()
print('\n'.join(cleaned))
"
EOF

chmod +x /tmp/clean_msg

# Executar git filter-branch
FILTER_BRANCH_SQUELCH_WARNING=1
git filter-branch -f --msg-filter '/tmp/clean_msg' --tag-name-filter cat -- --all

# Limpar backup
rm -rf .git/refs/original/

echo "✅ Histórico reescrito com sucesso."
echo ""
echo "Agora execute:"
echo "1. git push origin --force --all"
echo "2. git push origin --force --tags"
echo ""
echo "AVISO: Todos os colaboradores precisarão clonar novamente o repositório."
