import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.main import create_app

app = create_app()

if __name__ == '__main__':
    host = os.environ.get('APP_HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('APP_DEBUG', 'true').lower() == 'true'
    app.run(host=host, port=port, debug=debug)
