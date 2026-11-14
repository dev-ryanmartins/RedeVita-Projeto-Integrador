import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, 'backend')

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from backend.main import create_app


app = create_app()

if __name__ == '__main__':
    host = os.environ.get('APP_HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('APP_DEBUG', 'false').lower() == 'true'
    app.run(host=host, port=port, debug=debug)
