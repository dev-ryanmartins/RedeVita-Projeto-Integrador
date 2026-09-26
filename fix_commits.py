#!/usr/bin/env python3
"""
Script para limpar histórico Git de menções de bots de IA
Versão Windows - usa paths absolutos
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
    print("WARNING: This script rewrites Git history.")
    print("Make sure you have backed up the repository.")
    print("")
    
    # Caminho absoluto do script de limpeza
    script_dir = os.path.dirname(os.path.abspath(__file__))
    clean_script = os.path.join(script_dir, "clean_msg_wrapper.py")
    
    # Usar git filter-branch com caminho absoluto
    cmd = f'git filter-branch -f --msg-filter "python {clean_script}" --tag-name-filter cat -- --all'
    
    print("Executing history cleanup...")
    print("This may take a few minutes...")
    
    stdout, stderr, code = run_command(cmd)
    
    if code == 0:
        print("History rewritten successfully.")
        
        # Limpar backup
        run_command("rm -rf .git/refs/original/")
        
        print("Backup cleaned.")
        print("")
        print("Now execute:")
        print("1. git push origin --force --all")
        print("2. git push origin --force --tags")
    else:
        print("Error rewriting history:")
        print(stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
