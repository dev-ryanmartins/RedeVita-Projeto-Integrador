"""Alias de `seed_apresentacao.py` para criar/repopular as contas de demonstração.

Mantido por compatibilidade: qualquer chamada a este script é redirecionada para
`seed_apresentacao.py`, que cria TODAS as contas de teste já prontas para uso
(`senha_trocada=True`) e suporta a flag `--reset`.

Uso:
    python criar_contas_teste.py            # popula/atualiza (idempotente)
    python criar_contas_teste.py --reset    # limpa e repopula do zero
"""

import os
import runpy
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SEED = os.path.join(BASE_DIR, "seed_apresentacao.py")


if __name__ == "__main__":
    # Repassa os argumentos recebidos (ex.: --reset) para o script principal.
    sys.argv = [SEED] + sys.argv[1:]
    runpy.run_path(SEED, run_name="__main__")
