#!/usr/bin/env python3
import sys
import os

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

if __name__ == '__main__':
    msg = sys.stdin.read()
    cleaned = clean_message(msg)
    sys.stdout.write(cleaned)
