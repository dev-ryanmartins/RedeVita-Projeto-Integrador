#!/usr/bin/env python3
"""
Script automático para limpar histórico Git de menções de bots de IA
"""

import subprocess
import sys
import os
import re

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
    
    # Obter lista de commits que precisam de limpeza
    stdout, stderr, code = run_command("git log --all --pretty=format:'%H %s'")
    
    if code != 0:
        print("Erro ao obter commits:", stderr)
        sys.exit(1)
    
    commits = stdout.strip().split('\n')
    commits_to_clean = []
    
    for line in commits:
        if 'Devin' in line or 'bot' in line.lower():
            commit_hash = line.split()[0]
            commits_to_clean.append(commit_hash)
    
    if not commits_to_clean:
        print("✅ Nenhum commit com menções de bot encontrado.")
        sys.exit(0)
    
    print(f"Encontrados {len(commits_to_clean)} commits para limpar.")
    print("")
    
    # Limpar cada commit usando git commit --amend
    for i, commit in enumerate(commits_to_clean):
        print(f"Processando commit {i+1}/{len(commits_to_clean)}: {commit[:8]}...")
        
        # Obter mensagem atual
        stdout, stderr, code = run_command(f"git show -s --format=%B {commit}")
        if code != 0:
            print(f"  → Erro ao obter mensagem: {stderr}")
            continue
        
        original_msg = stdout
        cleaned_msg = clean_message(original_msg)
        
        # Se não houver mudança, pular
        if cleaned_msg == original_msg:
            print("  → Sem mudanças necessárias")
            continue
        
        # Fazer checkout do commit
        stdout, stderr, code = run_command(f"git checkout {commit}")
        if code != 0:
            print(f"  → Erro ao fazer checkout: {stderr}")
            continue
        
        # Reescrever mensagem
        stdout, stderr, code = run_command(f'git commit --amend -m "{cleaned_msg}"')
        if code != 0:
            print(f"  → Erro ao reescrever commit: {stderr}")
            continue
        
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
