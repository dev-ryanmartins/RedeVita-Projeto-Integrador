import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.main import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
