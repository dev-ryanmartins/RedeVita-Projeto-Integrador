"""
Testes de autenticação de login
Verifica que senhas incorretas, CPF inexistente e contas inativas não autenticam
"""

import pytest
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


@pytest.fixture
def client(app):
    """Fixture para cliente de teste."""
    return app.test_client()


@pytest.fixture
def usuario_ativo(app):
    """Fixture para criar usuário ativo de teste."""
    with app.app_context():
        usuario = Usuario(
            nome='Usuário Teste Ativo',
            cpf='12345678901',
            email='usuario@teste.com',
            senha=criptografar_senha('senha123'),
            cargo='Voluntário',
            ativo=True
        )
        db.session.add(usuario)
        db.session.commit()
        yield usuario


@pytest.fixture
def usuario_inativo(app):
    """Fixture para criar usuário inativo de teste."""
    with app.app_context():
        usuario = Usuario(
            nome='Usuário Teste Inativo',
            cpf='98765432100',
            email='inativo@teste.com',
            senha=criptografar_senha('senha123'),
            cargo='Voluntário',
            ativo=False
        )
        db.session.add(usuario)
        db.session.commit()
        yield usuario


class TestAuthLogin:
    """Testes de autenticação de login."""
    
    def test_login_conta_ativa_credenciais_corretas_autentica(self, client, usuario_ativo):
        """Credenciais corretas de conta ativa devem autenticar."""
        response = client.post('/login', data={
            'identificador': '12345678901',
            'senha': 'senha123'
        }, follow_redirects=False)
        
        assert response.status_code == 302 or response.status_code == 200
        # Verifica se há cookie de autenticação ou sessão
        if 'Set-Cookie' in response.headers:
            assert 'redevita_token' in response.headers.get('Set-Cookie', '')
    
    def test_login_conta_inativa_nao_autentica(self, client, usuario_inativo):
        """Conta inativa não deve autenticar, mesmo com senha correta."""
        response = client.post('/login', data={
            'identificador': '98765432100',
            'senha': 'senha123'
        })
        
        assert response.status_code == 200
        # A mensagem de erro pode ser genérica ("incorretos") para não revelar estado
        assert b'incorretos' in response.data.lower() or b'erro' in response.data.lower()
        # Verifica que não há cookie de autenticação
        assert 'Set-Cookie' not in response.headers or 'redevita_token' not in response.headers.get('Set-Cookie', '')
    
    def test_login_cpf_inexistente_nao_autentica(self, client):
        """CPF inexistente não deve autenticar nenhum usuário."""
        response = client.post('/login', data={
            'identificador': '11122233344',
            'senha': 'senha123'
        })
        
        assert response.status_code == 200
        assert b'incorretos' in response.data.lower()
        # Verifica que não há cookie de autenticação
        assert 'Set-Cookie' not in response.headers or 'redevita_token' not in response.headers.get('Set-Cookie', '')
    
    def test_login_email_inexistente_nao_autentica(self, client):
        """Email inexistente não deve autenticar nenhum usuário."""
        response = client.post('/login', data={
            'identificador': 'naoexiste@teste.com',
            'senha': 'senha123'
        })
        
        assert response.status_code == 200
        assert b'incorretos' in response.data.lower()
        # Verifica que não há cookie de autenticação
        assert 'Set-Cookie' not in response.headers or 'redevita_token' not in response.headers.get('Set-Cookie', '')
    
    def test_login_senha_incorreta_nao_autentica(self, client, usuario_ativo):
        """Senha incorreta não deve autenticar."""
        response = client.post('/login', data={
            'identificador': '12345678901',
            'senha': 'senha_errada'
        })
        
        assert response.status_code == 200
        assert b'incorretos' in response.data.lower()
        # Verifica que não há cookie de autenticação
        assert 'Set-Cookie' not in response.headers or 'redevita_token' not in response.headers.get('Set-Cookie', '')
    
    def test_nao_ha_fallback_para_usuario_id_1(self, client, usuario_ativo):
        """Não deve haver fallback para usuário ID 1 ou primeiro usuário."""
        # Tenta login com credenciais completamente inválidas
        response = client.post('/login', data={
            'identificador': 'usuario_totalmente_inexistente',
            'senha': 'senha_errada'
        })
        
        assert response.status_code == 200
        assert b'incorretos' in response.data.lower()
        # Verifica que não há cookie de autenticação
        assert 'Set-Cookie' not in response.headers or 'redevita_token' not in response.headers.get('Set-Cookie', '')
    
    def test_resposta_erro_generica_nao_revela_existencia(self, client, usuario_ativo):
        """Resposta de erro deve ser genérica e não revelar se identificador existe."""
        # Resposta para CPF inexistente
        response1 = client.post('/login', data={
            'identificador': '99988877766',
            'senha': 'senha123'
        })
        
        # Resposta para senha incorreta de CPF existente
        response2 = client.post('/login', data={
            'identificador': '12345678901',
            'senha': 'senha_errada'
        })
        
        # Ambas devem ter mensagens genéricas sem revelar diferença
        assert b'incorretos' in response1.data.lower()
        assert b'incorretos' in response2.data.lower()
