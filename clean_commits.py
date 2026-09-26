#!/usr/bin/env python3
"""
Script para limpar histórico Git de menções de bots de IA
"""

import subprocess
import sys
import os

def run_command(cmd):
    """Executa comando e retorna output"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout, result.stderr, result.returncode

def main():
    print("⚠️  AVISO: Este script reescreve o histórico Git.")
    print("Certifique-se de ter feito backup do repositório.")
    print("")
    
    # Usar git filter-branch com script inline
    print("Iniciando limpeza do histórico...")
    
    # Comando mais simples que funciona no Windows
    cmd = '''git filter-branch -f --msg-filter '
    sed "/Co-authored-by.*bot/d" | sed "/Generated with \\[Devin\\]/d" | sed "/^$/N" | sed "/^\\n$/D"
' --tag-name-filter cat -- --all'''
    
    stdout, stderr, code = run_command(cmd)
    
    if code == 0:
        print("✅ Histórico reescrito com sucesso.")
        
        # Limpar backup
        run_command("rm -rf .git/refs/original/")
        
        print("✅ Backup limpo.")
        print("")
        print("Agora execute:")
        print("1. git push origin --force --all")
        print("2. git push origin --force --tags")
    else:
        print("❌ Erro ao reescrever histórico:")
        print(stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
