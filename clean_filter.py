#!/usr/bin/env python3
import sys

msg = sys.stdin.read()
lines = msg.split('\n')
cleaned = []

for line in lines:
    # Remover todas as linhas Co-authored-by
    if line.strip().startswith('Co-authored-by'):
        continue
    # Remover linha Generated with
    if 'Generated with [Devin]' in line:
        continue
    # Remover linhas vazias consecutivas
    if line.strip() == '' and cleaned and cleaned[-1].strip() == '':
        continue
    cleaned.append(line)

# Remover linhas vazias no final
while cleaned and cleaned[-1].strip() == '':
    cleaned.pop()

print('\n'.join(cleaned))
