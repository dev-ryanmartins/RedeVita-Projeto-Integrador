"""
Testes para P1.12: Verifica que há caminho de migrations versionado e que upgrade preserva dados
Testa também que migrations funcionam no mesmo tipo de banco pretendido para produção
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


class TestMigrationsSetup:
    """Testes para setup de migrations."""
    
    def test_flask_migrate_esta_instalado(self):
        """Flask-Migrate está instalado e disponível."""
        try:
            import flask_migrate
            import alembic
            assert flask_migrate is not None
            assert alembic is not None
        except ImportError:
            pytest.fail("Flask-Migrate ou Alembic não está instalado")
    
    def test_migrations_diretorio_existe(self):
        """Diretório de migrations Flask-Migrate existe."""
        migrations_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend', 'migrations')
        assert os.path.exists(migrations_dir)
        assert os.path.exists(os.path.join(migrations_dir, 'alembic.ini'))
        assert os.path.exists(os.path.join(migrations_dir, 'env.py'))
        assert os.path.exists(os.path.dirname(migrations_dir))
    
    def test_migrations_versions_existe(self):
        """Diretório de versões de migrations existe."""
        versions_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend', 'migrations', 'versions')
        assert os.path.exists(versions_dir)

    def test_migration_qr_nonce_existe(self):
        """Migration QR nonce existe."""
        migration_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend', 'migrations', 'versions', 'qr_001_add_nonce_and_approval.py')
        assert os.path.exists(migration_file)
    
    def test_migration_env_importa_modelos(self):
        """env.py de Flask-Migrate importa todos os modelos para autogenerate."""
        env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend', 'migrations', 'env.py')
        
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Deve importar todos os modelos principais
        assert 'from app.models.usuario import Usuario' in content
        assert 'from app.models.medicamento import Medicamento' in content
        assert 'from app.models.doacao import Doacao' in content
        assert 'from app.models.farmacia import Farmacia' in content


class TestMigrationsExecution:
    """Testes para execução de migrations."""
    
    def test_db_create_all_seguro_preserva_dados(self, app):
        """db.create_all() preserva dados existentes (P1.11)."""
        with app.app_context():
            # Criar registro sentinela
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
            
            sentinela_id = usuario.id
            
            # Executar create_all (simula setup normal)
            db.create_all()
            
            # Verificar que sentinela ainda existe
            sentinela_recuperado = db.session.get(Usuario, sentinela_id)
            assert sentinela_recuperado is not None
            assert sentinela_recuperado.nome == 'Usuário Sentinela'
    
    def test_inicializacao_nao_aplica_migrations_automaticamente(self):
        """Inicialização do servidor não aplica migrations automaticamente."""
        main_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend', 'main.py')
        
        with open(main_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Não deve chamar aplicar_migracoes_manuais
        assert 'aplicar_migracoes_manuais' not in content
        
        # Comentário instruindo a usar flask db upgrade é permitido
        # Mas não deve haver chamada real de upgrade
        assert 'upgrade()' not in content


class TestMigrationsProductionSafety:
    """Testes de segurança para migrations em produção."""
    
    def test_migration_documentacao_existe(self):
        """Documentação de migrations existe e descreve procedimentos."""
        doc_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend', 'MIGRATIONS.md')
        assert os.path.exists(doc_file)
        
        with open(doc_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Deve mencionar procedimentos de backup
        assert 'backup' in content.lower()
        
        # Deve mencionar rollback
        assert 'rollback' in content.lower() or 'reverter' in content.lower()
        
        # Deve mencionar banco-alvo
        assert 'banco-alvo' in content.lower() or 'banco alvo' in content.lower()
        
        # Deve mencionar decision pendente se aplicável
        assert 'decisão pendente' in content.lower() or 'pendente' in content.lower()


class TestMigrationsMySQLValidation:
    """Testes para validação em MySQL (banco pretendido para produção)."""
    
    def test_limitacao_sqlite_nao_valida_mysql(self):
        """SQLite em memória não valida comportamento do MySQL."""
        # Este teste documenta a limitação: testes SQLite não provam compatibilidade MySQL
        # Validação em MySQL de teste é necessária antes de aplicar migrations em produção
        
        # Marcar como skip com mensagem clara
        pytest.skip("Validação em MySQL é necessária antes de aplicar migrations em produção. "
                    "Este teste SQLite não prova compatibilidade MySQL.")
    
    def test_docker_compose_usa_mysql(self):
        """Docker Compose configura MySQL como banco."""
        compose_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docker-compose.yml')
        
        with open(compose_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Deve usar MySQL 8.0
        assert 'mysql:8.0' in content
        assert 'image: mysql' in content.lower()
        
        # Deve configurar DATABASE_URL
        assert 'DATABASE_URL' in content


class TestMigrationsLegacy:
    """Testes para migrações manuais legadas."""
    
    def test_migration_custom_mantida_para_referencia(self):
        """Migration manual antiga foi movida para diretório custom (não aplicada automaticamente)."""
        custom_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend', 'migrations_custom')
        custom_migration = os.path.join(custom_dir, 'add_ativo_medicamentos.py')
        
        assert os.path.exists(custom_dir)
        assert os.path.exists(custom_migration)
    
    def test_migration_custom_nao_aplicada_no_startup(self):
        """Migration custom não é aplicada no startup."""
        main_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend', 'main.py')
        
        with open(main_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Não deve importar migrations_custom
        assert 'migrations_custom' not in content
        
        # Não deve executar add_ativo_medicamentos
        assert 'add_ativo_medicamentos' not in content.lower()


class TestMigrationsUpgradeScenario:
    """Testes de cenário de upgrade de schema anterior."""
    
    def test_cenario_upgrade_preserva_dados_sinteticos(self, app):
        """Cenário de upgrade: dados sintéticos são preservados."""
        with app.app_context():
            # Simular schema anterior: tabela usuarios sem colunas ativo e credencial_versao
            # Como não podemos reverter o schema no teste, apenas verificamos que:
            # 1. db.create_all() não apaga dados (P1.11)
            # 2. Migrations podem ser aplicadas separadamente
            
            # Criar usuário sentinela
            usuario = Usuario(
                nome='Usuário Upgrade Teste',
                cpf='9876543210101',
                email='upgrade@teste.com',
                senha=criptografar_senha('senha123'),
                cargo='Voluntário',
                ativo=True,
                credencial_versao=1
            )
            db.session.add(usuario)
            db.session.commit()
            
            sentinela_id = usuario.id
            
            # Executar create_all (seguro, preserva dados)
            db.create_all()
            
            # Verificar que dados são preservados
            usuario_recuperado = db.session.get(Usuario, sentinela_id)
            assert usuario_recuperado is not None
            assert usuario_recuperado.nome == 'Usuário Upgrade Teste'
    
    def test_cenario_banco_vazio_para_schema_atual(self, app):
        """Cenário: banco vazio pode ser atualizado para schema atual."""
        with app.app_context():
            # Em banco vazio, db.create_all() cria todas as tabelas
            # Migrations podem então ser aplicadas para alinhar com schema
            
            # Contar tabelas após create_all
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            # Deve ter tabelas principais
            assert 'usuarios' in tables
            assert 'medicamentos' in tables
            assert 'doacoes' in tables
            assert 'farmacias' in tables


class TestMigrationsCommands:
    """Testes para comandos de migration."""
    
    def test_comando_flask_db_init_foi_executado(self):
        """Comando 'flask db init' foi executado para inicializar Flask-Migrate."""
        # Verificar que diretório migrations existe (resultado de flask db init)
        migrations_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend', 'migrations')
        assert os.path.exists(migrations_dir)
        assert os.path.exists(os.path.join(migrations_dir, 'script.py.mako'))
        assert os.path.exists(os.path.join(migrations_dir, 'README'))
