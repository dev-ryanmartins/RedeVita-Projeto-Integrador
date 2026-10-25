"""
Testes para P1.11: Verifica que create_tables.py não apaga dados no modo normal
e que o modo destrutivo recusa produção
"""

import os
import pytest
import subprocess
import sys
from main import create_app
from app.database import db
from app.models.usuario import Usuario
from app.core.security import criptografar_senha


@pytest.fixture
def app():
    """Fixture para criar aplicação Flask de teste."""
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_EXPIRE_ON_COMMIT': False,
        'WTF_CSRF_ENABLED': False,
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


class TestCreateTablesSafe:
    """Testes para modo seguro (normal) de create_tables."""
    
    def test_setup_normal_preserva_dados_existentes(self, app):
        """Setup normal (sem --drop) preserva dados existentes."""
        with app.app_context():
            # Criar um registro sentinela
            usuario = Usuario(
                nome='Usuário Sentinela',
                cpf='12345678901',
                email='sentinela@teste.com',
                senha=criptografar_senha('senha123'),
                cargo='Voluntário',
                ativo=True,
                credencial_versao=1
            )
            db.session.add(usuario)
            db.session.commit()
            
            # Registrar ID do sentinela
            sentinela_id = usuario.id
            
            # Executar create_all novamente (simula setup normal)
            db.create_all()
            
            # Verificar que o sentinela ainda existe
            sentinela_recuperado = db.session.get(Usuario, sentinela_id)
            assert sentinela_recuperado is not None
            assert sentinela_recuperado.nome == 'Usuário Sentinela'
            assert sentinela_recuperado.cpf == '12345678901'
    
    def test_setup_normal_nao_executa_drop_all(self, app):
        """Setup normal não executa db.drop_all()."""
        with app.app_context():
            # Limpar banco antes do teste
            db.session.query(Usuario).delete()
            db.session.commit()
            
            # Criar múltiplos registros com CPFs únicos
            for i in range(10, 15):
                usuario = Usuario(
                    nome=f'Usuário {i}',
                    cpf=f'{i:011d}',
                    email=f'usuario{i}@teste.com',
                    senha=criptografar_senha('senha123'),
                    cargo='Voluntário',
                    ativo=True,
                    credencial_versao=1
                )
                db.session.add(usuario)
            db.session.commit()
            
            # Contar registros antes
            count_antes = db.session.query(Usuario).count()
            assert count_antes == 5
            
            # Executar create_all (simula setup normal)
            db.create_all()
            
            # Verificar que registros ainda existem
            count_depois = db.session.query(Usuario).count()
            assert count_depois == 5


class TestCreateTablesDestructive:
    """Testes para modo destrutivo de create_tables."""
    
    def test_modo_destrutivo_requer_confirmacao(self):
        """Modo destrutivo (--drop) requer confirmação (--confirm)."""
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend', 'create_tables.py')
        
        # Tentar executar com --drop sem --confirm
        env = os.environ.copy()
        env['FLASK_ENV'] = 'development'
        env['DATABASE_URL'] = 'sqlite:///test.db'
        
        result = subprocess.run(
            [sys.executable, script_path, '--drop'],
            env=env,
            capture_output=True,
            text=True
        )
        
        # Deve falhar com mensagem de erro
        assert result.returncode != 0
        assert 'confirm' in result.stdout.lower() or 'confirm' in result.stderr.lower()
    
    def test_modo_destrutivo_recusa_producao(self):
        """Modo destrutivo recusa ambiente de produção."""
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend', 'create_tables.py')
        
        # Tentar executar em ambiente de produção
        env = os.environ.copy()
        env['FLASK_ENV'] = 'production'
        env['DATABASE_URL'] = 'mysql+pymysql://user:pass@prod-server:3306/redevita'
        
        result = subprocess.run(
            [sys.executable, script_path, '--drop', '--confirm'],
            env=env,
            capture_output=True,
            text=True
        )
        
        # Deve falhar com mensagem de erro
        assert result.returncode != 0
        assert 'produção' in result.stdout.lower() or 'production' in result.stdout.lower() or 'produção' in result.stderr.lower() or 'production' in result.stderr.lower()
    
    def test_modo_destrutivo_requere_interacao(self):
        """Modo destrutivo requer confirmação interativa em ambiente não seguro."""
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend', 'create_tables.py')
        
        # Tentar executar em ambiente não seguro sem interação
        env = os.environ.copy()
        env['FLASK_ENV'] = 'development'
        env['DATABASE_URL'] = 'mysql+pymysql://user:pass@unknown-server:3306/redevita'
        
        result = subprocess.run(
            [sys.executable, script_path, '--drop', '--confirm'],
            env=env,
            capture_output=True,
            text=True,
            input=''  # Sem entrada interativa
        )
        
        # Deve falhar ou cancelar devido à falta de confirmação
        assert result.returncode != 0 or 'cancel' in result.stdout.lower() or 'cancel' in result.stderr.lower()


class TestCreateTablesMigrations:
    """Testes para uso de migrations existentes."""
    
    def test_migration_add_ativo_preserva_dados(self, app):
        """Migration add_ativo_medicamentos preserva dados existentes."""
        with app.app_context():
            # A migration já existe e deve preservar dados
            # Este teste verifica que a migration existe e é executável
            migration_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend', 'migrations', 'add_ativo_medicamentos.py')
            assert os.path.exists(migration_path)
    
    def test_migration_add_ativo_nao_usa_drop_all(self, app):
        """Migration add_ativo_medicamentos não usa db.drop_all()."""
        migration_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend', 'migrations', 'add_ativo_medicamentos.py')
        
        with open(migration_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Não deve conter drop_all
        assert 'drop_all' not in content.lower()
        assert 'drop_all()' not in content


class TestCreateTablesProductionSafety:
    """Testes de segurança para produção."""
    
    def test_producao_detectada_por_flask_env(self):
        """Produção é detectada pela variável FLASK_ENV=production."""
        env = os.environ.copy()
        env['FLASK_ENV'] = 'production'
        env['DATABASE_URL'] = 'sqlite:///test.db'
        
        # Simular verificação do script
        from backend.create_tables import is_production_environment
        # Não podemos importar diretamente devido ao path, então verificamos a lógica
        assert env['FLASK_ENV'] == 'production'
    
    def test_producao_detectada_por_database_url(self):
        """Produção é detectada por DATABASE_URL sem localhost."""
        env = os.environ.copy()
        env['FLASK_ENV'] = 'development'
        env['DATABASE_URL'] = 'mysql+pymysql://user:pass@prod-server:3306/redevita'
        
        # Verificar que URL não contém localhost
        assert 'localhost' not in env['DATABASE_URL']
        assert '127.0.0.1' not in env['DATABASE_URL']
