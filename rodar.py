"""Inicializador local do RedeVita para apresentação e desenvolvimento.

Execute com:
    python rodar.py

Ele abre o sistema no navegador usando localhost, sem precisar acessar pelo IP da rede.
"""

import os
import sys
import threading
import webbrowser
from pathlib import Path

BASE_DIR = str(Path(__file__).resolve().parent)
BACKEND_DIR = os.path.join(BASE_DIR, 'backend')

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from backend.main import create_app


HOST = os.environ.get('APP_HOST', '127.0.0.1')
PORT = int(os.environ.get('PORT', 5000))
DEBUG = os.environ.get('APP_DEBUG', 'true').lower() == 'true'
OPEN_BROWSER = os.environ.get('OPEN_BROWSER', 'true').lower() == 'true'

app = create_app()


def _abrir_navegador():
    url = f'http://localhost:{PORT}' if HOST in (
        '127.0.0.1', 'localhost') else f'http://{HOST}:{PORT}'
    webbrowser.open_new(url)


if __name__ == '__main__':
    if OPEN_BROWSER:
        threading.Timer(1.0, _abrir_navegador).start()

    print('')
    print('====================================================')
    print('  RedeVita rodando em modo local')
    print('====================================================')
    print(f'  Abra: http://localhost:{PORT}')
    print('  Login inicial: 000.000.000-00 / admin123')
    print('  Pressione CTRL+C para encerrar.')
    print('')

    app.run(host=HOST, port=PORT, debug=DEBUG, use_reloader=False)
