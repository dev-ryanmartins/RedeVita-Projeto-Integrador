#!/usr/bin/env python3
"""
Script para limpar histórico Git de menções de bots de IA
Usa git rebase em lote para reescrever mensagens de commit
"""

import subprocess
import sys
import os

def run_command(cmd):
    """Executa comando e retorna output"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout, result.stderr, result.returncode

def clean_message(msg):
    """Remove linhas indesejadas da mensagem de commit"""
    lines = msg.split('\n')
    cleaned = []
    
    for line in lines:
        # Remover linhas de Co-authored-by que mencionam bot
        if 'Co-authored-by' in line and 'bot' in line.lower():
            continue
        # Remover linha "Generated with [Devin]"
        if 'Generated with [Devin]' in line:
            continue
        # Remover linhas vazias consecutivas
        if line.strip() == '' and cleaned and cleaned[-1].strip() == '':
            continue
        cleaned.append(line)
    
    # Remover linhas vazias no final
    while cleaned and cleaned[-1].strip() == '':
        cleaned.pop()
    
    return '\n'.join(cleaned)

def main():
    print("⚠️  AVISO: Este script reescreve o histórico Git.")
    print("Certifique-se de ter feito backup do repositório.")
    print("")
    
    # Obter lista de commits
    stdout, stderr, code = run_command("git log --all --pretty=format:'%H'")
    
    if code != 0:
        print("Erro ao obter commits:", stderr)
        sys.exit(1)
    
    commits = stdout.strip().split('\n')
    print(f"Encontrados {len(commits)} commits para processar.")
    
    # Reescrever cada commit
    for i, commit in enumerate(commits):
        print(f"Processando commit {i+1}/{len(commits)}: {commit[:8]}...")
        
        # Obter mensagem atual
        stdout, stderr, code = run_command(f"git show -s --format=%B {commit}")
        if code != 0:
            print(f"Erro ao obter mensagem do commit {commit}: {stderr}")
            continue
        
        original_msg = stdout
        cleaned_msg = clean_message(original_msg)
        
        # Se não houver mudança, pular
        if cleaned_msg == original_msg:
            print("  → Sem mudanças necessárias")
            continue
        
        # Reescrever mensagem
        with open('.git/COMMIT_EDITMSG', 'w') as f:
            f.write(cleaned_msg)
        
        # Usar git commit --amend para reescrever
        run_command(f"git checkout {commit}")
        run_command("git commit --amend -F .git/COMMIT_EDITMSG")
        
        print("  → Mensagem reescrita")
    
    # Voltar para o branch original
    stdout, stderr, code = run_command("git branch --show-current")
    original_branch = stdout.strip()
    run_command(f"git checkout {original_branch}")
    
    print("\n✅ Histórico reescrito com sucesso.")
    print("Agora execute:")
    print("1. git push origin --force --all")
    print("2. git push origin --force --tags")

if __name__ == '__main__':
    main()
