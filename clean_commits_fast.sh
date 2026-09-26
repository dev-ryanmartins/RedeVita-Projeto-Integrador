#!/bin/bash
# Script rápido para limpar commits usando git rebase automático

echo "Iniciando limpeza de commits..."

# Criar script de edição automática
cat > /tmp/edit_msg.sh << 'EOF'
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

chmod +x /tmp/edit_msg.sh

# Rebase com script automático
FILTER_BRANCH_SQUELCH_WARNING=1
git filter-branch -f --msg-filter '/tmp/edit_msg.sh' --tag-name-filter cat -- --all

rm -rf .git/refs/original/

echo "Historico limpo."
echo "Execute: git push origin --force --all"
