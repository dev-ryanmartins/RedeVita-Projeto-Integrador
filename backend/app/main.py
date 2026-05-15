from flask import Flask, render_template
from flask_login import LoginManager
from app.config import Config
from app.database import init_db
from app.models.usuario import Usuario

# Importando as rotas (Blueprints)
from app.routes.auth import auth_bp
from app.routes.inventario import inventory_bp

def create_app():
    app = Flask(__name__, 
                template_folder='../../frontend/templates', 
                static_folder='../../frontend/static')
    
    app.config.from_object(Config)

    # Inicializa Banco de Dados
    init_db(app)

    # Configura o LoginManager
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    # Registra as rotas
    app.register_blueprint(auth_bp)
    app.register_blueprint(inventory_bp)

    @app.route('/')
    def index():
        return render_template('login.html')

    return app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)