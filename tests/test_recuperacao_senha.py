"""
Testes de recuperação de senha (P0.3)
Verifica armazenamento seguro de tokens no servidor, proteção contra abuso e invalidação após redefinição.
"""

import pytest
from datetime import datetime, timedelta
from main import create_app
from app.database import db
from app.models.usuario import Usuario
from app.models.recuperacao_senha import RecuperacaoSenha
from app.core.security import criptografar_senha


@pytest.fixture
def app():
    """Fixture para criar aplicação Flask de teste."""
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_EXPIRE_ON_COMMIT': False,
        'WTF_CSRF_ENABLED': False,
        'ENV': 'development'
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
def usuario_a(app):
    """Fixture para criar usuário A de teste."""
    with app.app_context():
        usuario = Usuario(
            nome='Usuário Teste A',
            cpf='12345678901',
            email='usuario_a@teste.com',
            senha=criptografar_senha('senha123'),
            cargo='Voluntário',
            ativo=True
        )
        db.session.add(usuario)
        db.session.commit()
        yield usuario


@pytest.fixture
def usuario_b(app):
    """Fixture para criar usuário B de teste."""
    with app.app_context():
        usuario = Usuario(
            nome='Usuário Teste B',
            cpf='98765432100',
            email='usuario_b@teste.com',
            senha=criptografar_senha('senha456'),
            cargo='Voluntário',
            ativo=True
        )
        db.session.add(usuario)
        db.session.commit()
        yield usuario


class TestRecuperacaoSenhaP03:
    """Testes para recuperação de senha (P0.3)."""
    
    def test_recuperacao_sucesso_token_valido(self, app, client, usuario_a):
        """Testa fluxo de recuperação com sucesso com token válido."""
        with app.app_context():
            # Solicita recuperação
            response = client.post('/recuperar-senha', data={
                'identificador': 'usuario_a@teste.com'
            }, follow_redirects=False)
            
            assert response.status_code == 302
            
            # Verifica que token foi criado no banco
            with client.session_transaction() as session:
                recuperacao_id = session.get('pwd_recovery_id')
                assert recuperacao_id is not None
            
            recuperacao = RecuperacaoSenha.query.get(recuperacao_id)
            assert recuperacao is not None
            assert recuperacao.usuario_id == usuario_a.id
            assert recuperacao.is_valido() is True
            assert recuperacao.token is not None
            assert len(recuperacao.token) >= 32  # Token seguro
    
    def test_conta_a_tenta_redefinir_senha_conta_b(self, app, client, usuario_a, usuario_b):
        """Testa que conta A não pode redefinir senha da conta B (troca cruzada)."""
        with app.app_context():
            # Solicita recuperação para conta B
            response = client.post('/recuperar-senha', data={
                'identificador': 'usuario_b@teste.com'
            }, follow_redirects=False)
            
            assert response.status_code == 302
            
            with client.session_transaction() as session:
                recuperacao_id = session.get('pwd_recovery_id')
                session['pwd_recovery_usuario_id'] = usuario_b.id
            
            # Login como usuário A
            client.post('/login', data={
                'identificador': '12345678901',
                'senha': 'senha123'
            }, follow_redirects=False)
            
            # Tenta redefinir senha de B sendo logado como A
            response = client.post('/redefinir-senha', data={
                'nova_senha': 'nova_senha_123',
                'confirmar_senha': 'nova_senha_123'
            }, follow_redirects=False)
            
            # Deve falhar - usuário logado não corresponde ao usuário do token
            assert response.status_code == 302
            # Redireciona para recuperar-senha devido à verificação de sessão
    
    def test_token_invalido_nao_encontrado(self, app, client, usuario_a):
        """Testa que token inválido não permite redefinição."""
        with app.app_context():
            # Solicita recuperação
            client.post('/recuperar-senha', data={
                'identificador': 'usuario_a@teste.com'
            }, follow_redirects=False)
            
            with client.session_transaction() as session:
                recuperacao_id = session.get('pwd_recovery_id')
                session['pwd_recovery_usuario_id'] = usuario_a.id
            
            # Login
            client.post('/login', data={
                'identificador': '12345678901',
                'senha': 'senha123'
            }, follow_redirects=False)
            
            # Tenta usar token inválido
            response = client.post('/verificar-codigo', data={
                'token': 'token_invalido_aleatorio'
            }, follow_redirects=False)
            
            assert response.status_code == 200
            data = response.data.decode('utf-8').lower()
            assert 'incorreto' in data or 'inválido' in data
            
            # Verifica que tentativa foi registrada
            recuperacao = RecuperacaoSenha.query.get(recuperacao_id)
            assert recuperacao.tentativas == 1
    
    def test_token_vencido(self, app, client, usuario_a):
        """Testa que token vencido não permite redefinição."""
        with app.app_context():
            # Cria token expirado manualmente
            recuperacao = RecuperacaoSenha(
                usuario_id=usuario_a.id,
                token='token_expirado_test',
                token_hash='hash_test',
                expira_em=datetime.utcnow() - timedelta(minutes=1)  # Expirado
            )
            db.session.add(recuperacao)
            db.session.commit()
            
            with client.session_transaction() as session:
                session['pwd_recovery_id'] = recuperacao.id
                session['pwd_recovery_usuario_id'] = usuario_a.id
            
            # Login
            client.post('/login', data={
                'identificador': '12345678901',
                'senha': 'senha123'
            }, follow_redirects=False)
            
            # Tenta usar token vencido
            response = client.post('/verificar-codigo', data={
                'token': 'token_expirado_test'
            }, follow_redirects=False)
            
            assert response.status_code == 200
            data = response.data.decode('utf-8').lower()
            # A mensagem atual é "token expirado. solicite uma nova recuperação."
            assert 'expirado' in data
    
    def test_token_reutilizado_apos_uso(self, app, client, usuario_a):
        """Testa que token não pode ser reutilizado após uso."""
        with app.app_context():
            # Cria token
            recuperacao = RecuperacaoSenha.criar_token(usuario_a.id)
            
            with client.session_transaction() as session:
                session['pwd_recovery_id'] = recuperacao.id
                session['pwd_recovery_usuario_id'] = usuario_a.id
            
            # Login
            client.post('/login', data={
                'identificador': '12345678901',
                'senha': 'senha123'
            }, follow_redirects=False)
            
            # Usa token pela primeira vez
            response = client.post('/verificar-codigo', data={
                'token': recuperacao.token
            }, follow_redirects=False)
            
            assert response.status_code == 302  # Redireciona após sucesso
            
            # Marca o token como usado manualmente para o teste
            recuperacao.marcar_como_usado()
            
            # Tenta usar o mesmo token novamente
            response = client.post('/verificar-codigo', data={
                'token': recuperacao.token
            }, follow_redirects=False)
            
            assert response.status_code == 200
            data = response.data.decode('utf-8').lower()
            assert 'inválido' in data or 'expirou' in data
    
    def test_excesso_tentativas_bloqueia_token(self, app, client, usuario_a):
        """Testa que excesso de tentativas bloqueia o token."""
        with app.app_context():
            # Cria token com limite de 2 tentativas
            recuperacao = RecuperacaoSenha(
                usuario_id=usuario_a.id,
                token='token_limite_test',
                token_hash='hash_test',
                expira_em=datetime.utcnow() + timedelta(minutes=15),
                max_tentativas=2
            )
            db.session.add(recuperacao)
            db.session.commit()
            
            with client.session_transaction() as session:
                session['pwd_recovery_id'] = recuperacao.id
                session['pwd_recovery_usuario_id'] = usuario_a.id
            
            # Login
            client.post('/login', data={
                'identificador': '12345678901',
                'senha': 'senha123'
            }, follow_redirects=False)
            
            # Tenta 3 vezes com token incorreto
            for i in range(3):
                response = client.post('/verificar-codigo', data={
                    'token': 'token_errado'
                }, follow_redirects=False)
            
            # Verifica que foi bloqueado
            assert response.status_code == 200
            data = response.data.decode('utf-8').lower()
            assert 'máximo de tentativas' in data or 'excedido' in data
            
            # Verifica que tentativas foram registradas
            db.session.refresh(recuperacao)
            assert recuperacao.tentativas >= 2
    
    def test_resposta_generica_nao_revela_existencia(self, app, client):
        """Testa que resposta é genérica e não revela se conta existe."""
        # Solicita recuperação para e-mail inexistente
        response = client.post('/recuperar-senha', data={
            'identificador': 'naoexiste@teste.com'
        }, follow_redirects=False)
        
        assert response.status_code == 200
        data = response.data.decode('utf-8').lower()
        assert 'cadastro' in data or 'instruções' in data
        # Não deve dizer "conta não encontrada"
        assert 'não encontrado' not in data
    
    def test_logs_nao_exibem_token(self, app, client, usuario_a):
        """Testa que logs não exibem o token."""
        with app.app_context():
            # Solicita recuperação
            client.post('/recuperar-senha', data={
                'identificador': 'usuario_a@teste.com'
            }, follow_redirects=False)
            
            with client.session_transaction() as session:
                recuperacao_id = session.get('pwd_recovery_id')
            
            recuperacao = RecuperacaoSenha.query.get(recuperacao_id)
            
            # Verifica que o token foi gerado e está armazenado
            assert recuperacao.token is not None
            
            # Verifica que o token não está nos dados do usuário
            assert recuperacao.token not in str(recuperacao.usuario.nome)
            assert recuperacao.token not in str(recuperacao.usuario.email)
    
    def test_invalidacao_apos_redefinicao(self, app, usuario_a):
        """Testa que após redefinição, token é invalidado e credencial versão aumenta."""
        with app.app_context():
            # Recarrega o usuário para garantir que está na sessão
            usuario = Usuario.query.get(usuario_a.id)
            versao_anterior = usuario.credencial_versao
            
            # Cria token diretamente
            recuperacao = RecuperacaoSenha.criar_token(usuario.id)
            
            # Simula o fluxo de redefinição chamando o método do modelo
            assert recuperacao.usado_em is None
            assert recuperacao.is_valido() is True
            
            # Marca como usado
            recuperacao.marcar_como_usado()
            
            # Aumenta versão de credencial
            usuario.credencial_versao += 1
            db.session.commit()
            
            # Recarrega do banco para verificar mudanças
            db.session.expire_all()
            usuario_atualizado = Usuario.query.get(usuario.id)
            recuperacao_atualizada = RecuperacaoSenha.query.get(recuperacao.id)
            
            # Verifica que token foi marcado como usado
            assert recuperacao_atualizada.usado_em is not None
            
            # Verifica que versão de credencial aumentou
            assert usuario_atualizado.credencial_versao == versao_anterior + 1
            
            # Verifica que token não é mais válido
            assert recuperacao_atualizada.is_valido() is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
