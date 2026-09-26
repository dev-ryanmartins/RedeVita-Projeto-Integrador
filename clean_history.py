#!/usr/bin/env python3
"""
Script para limpar histórico Git de menções de bots de IA
Remove linhas de Co-authored-by e menções de ferramentas automatizadas
"""

import subprocess
import sys
import os

def run_command(cmd):
    """Executa comando e retorna output"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout, result.stderr, result.returncode

def clean_commit_message(message):
    """Remove linhas indesejadas da mensagem de commit"""
    lines = message.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Remover linhas de Co-authored-by
        if 'Co-authored-by' in line and 'bot' in line.lower():
            continue
        # Remover linha "Generated with [Devin]"
        if 'Generated with [Devin]' in line:
            continue
        # Remover linhas vazias consecutivas
        if line.strip() == '' and cleaned_lines and cleaned_lines[-1].strip() == '':
            continue
        cleaned_lines.append(line)
    
    # Remover linhas vazias no final
    while cleaned_lines and cleaned_lines[-1].strip() == '':
        cleaned_lines.pop()
    
    return '\n'.join(cleaned_lines)

def main():
    print("⚠️  AVISO: Este script reescreve o histórico Git.")
    print("Certifique-se de ter feito backup do repositório.")
    print("")
    
    confirm = input("Deseja continuar? (s/n): ")
    if confirm.lower() != 's':
        print("Operação cancelada.")
        sys.exit(0)
    
    print("Iniciando limpeza do histórico...")
    
    # Usar git filter-repo (mais seguro que filter-branch)
    # Primeiro, verificar se git-filter-repo está instalado
    stdout, stderr, code = run_command("git filter-repo --version")
    
    if code != 0:
        print("git-filter-repo não está instalado.")
        print("Instale com: pip install git-filter-repo")
        print("Ou use: brew install git-filter-repo (macOS)")
        print("Ou use: conda install -c conda-forge git-filter-repo")
        sys.exit(1)
    
    # Criar script de callback para git-filter-repo
    callback_script = """
import sys

def clean_message(msg):
    lines = msg.split('\\n')
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
    return '\\n'.join(cleaned)

msg = sys.stdin.read()
cleaned = clean_message(msg)
sys.stdout.write(cleaned)
"""
    
    # Salvar script temporário
    with open('.git/filter-repo-callback.py', 'w') as f:
        f.write(callback_script)
    
    print("Executando git filter-repo...")
    
    # Executar git filter-repo
    cmd = "git filter-repo --message-callback 'python .git/filter-repo-callback.py'"
    stdout, stderr, code = run_command(cmd)
    
    # Limpar script temporário
    if os.path.exists('.git/filter-repo-callback.py'):
        os.remove('.git/filter-repo-callback.py')
    
    if code == 0:
        print("✅ Histórico reescrito com sucesso.")
        print("")
        print("Agora execute:")
        print("1. git push origin --force --all")
        print("2. git push origin --force --tags")
        print("")
        print("AVISO: Todos os colaboradores precisarão clonar novamente o repositório.")
    else:
        print("❌ Erro ao reescrever histórico:")
        print(stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
