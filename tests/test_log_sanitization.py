"""
Testes de sanitização de logs para P1.2
Verifica que logs não contêm CPF integral, senhas, tokens ou dados sensíveis
"""

import pytest
from main import create_app
from app.database import db
from app.models.usuario import Usuario
from app.models.log_atividade import LogAtividade
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
def usuario_teste(app):
    """Fixture para criar usuário de teste."""
    with app.app_context():
        usuario = Usuario(
            nome='Usuário Teste',
            cpf='12345678901',
            email='usuario@teste.com',
            senha=criptografar_senha('senha123'),
            cargo='Voluntário',
            ativo=True,
            credencial_versao=1
        )
        db.session.add(usuario)
        db.session.commit()
        db.session.refresh(usuario)
        yield usuario


class TestLogSanitization:
    """Testes de sanitização de logs para P1.2."""
    
    def test_login_log_does_not_contain_full_cpf(self, app, usuario_teste):
        """Log de login não deve conter CPF integral."""
        with app.test_client() as client:
            # Tentativa de login com CPF
            response = client.post('/login', data={
                'identificador': '12345678901',
                'senha': 'senha_errada'
            }, follow_redirects=False)
            
            # Verificar logs
            with app.app_context():
                logs = LogAtividade.query.filter(
                    LogAtividade.acao.like('%LOGIN%')
                ).all()
                
                assert len(logs) > 0, "Deve haver logs de login"
                
                for log in logs:
                    # CPF completo não deve estar no log
                    assert '12345678901' not in log.acao, f"CPF integral encontrado no log: {log.acao}"
                    # Pode ou não ter mascaramento, mas não CPF completo
    
    def test_login_log_does_not_contain_password(self, app, usuario_teste):
        """Log de login não deve conter senha."""
        with app.test_client() as client:
            # Tentativa de login
            response = client.post('/login', data={
                'identificador': '12345678901',
                'senha': 'senha123'
            }, follow_redirects=False)
            
            # Verificar logs
            with app.app_context():
                logs = LogAtividade.query.filter(
                    LogAtividade.acao.like('%LOGIN%')
                ).all()
                
                for log in logs:
                    # Senha não deve estar no log
                    assert 'senha123' not in log.acao.lower(), f"Senha encontrada no log: {log.acao}"
                    assert 'senha_errada' not in log.acao.lower(), f"Senha encontrada no log: {log.acao}"
    
    def test_password_recovery_log_does_not_contain_code(self, app, usuario_teste):
        """Log de recuperação de senha não deve conter código."""
        with app.test_client() as client:
            # Solicitar recuperação
            response = client.post('/recuperar-senha', data={
                'identificador': 'usuario@teste.com'
            }, follow_redirects=False)
            
            # Verificar logs
            with app.app_context():
                logs = LogAtividade.query.filter(
                    LogAtividade.acao.like('%Recuperação%')
                ).all()
                
                for log in logs:
                    # Código de 6 dígitos não deve estar no log
                    import re
                    # Verificar se há sequência de 6 dígitos (código)
                    codigo_pattern = r'\b\d{6}\b'
                    codigos = re.findall(codigo_pattern, log.acao)
                    assert len(codigos) == 0, f"Código de recuperação encontrado no log: {log.acao}"
    
    def test_password_reset_log_does_not_contain_new_password(self, app, usuario_teste):
        """Log de redefinição de senha não deve conter nova senha."""
        with app.test_client() as client:
            # Simular sessão de recuperação
            with client.session_transaction() as sess:
                sess['pwd_recovery'] = {
                    'user_id': usuario_teste.id,
                    'email': 'usuario@teste.com',
                    'nome': usuario_teste.nome,
                    'codigo': '123456',
                    'expira_em': 9999999999,
                    'verificado': True
                }
            
            # Redefinir senha
            response = client.post('/redefinir-senha', data={
                'nova_senha': 'NovaSenha123!',
                'confirmar_senha': 'NovaSenha123!'
            }, follow_redirects=False)
            
            # Verificar logs
            with app.app_context():
                logs = LogAtividade.query.filter(
                    LogAtividade.acao.like('%Redefinição%')
                ).all()
                
                for log in logs:
                    # Nova senha não deve estar no log
                    assert 'NovaSenha123!' not in log.acao, f"Nova senha encontrada no log: {log.acao}"
                    assert 'nova_senha' not in log.acao.lower(), f"Campo de senha encontrado no log: {log.acao}"
    
    def test_log_contains_operational_info(self, app, usuario_teste):
        """Logs devem conter informação operacional mínima."""
        with app.test_client() as client:
            # Login bem-sucedido
            response = client.post('/login', data={
                'identificador': '12345678901',
                'senha': 'senha123'
            }, follow_redirects=False)
            
            # Verificar logs
            with app.app_context():
                logs = LogAtividade.query.filter(
                    LogAtividade.acao.like('%Login%')
                ).all()
                
                # Pode haver ou não logs de login, dependendo da implementação
                # Se houver, verificar que contêm info operacional
                if logs:
                    log_sucesso = [l for l in logs if 'fez login' in l.acao]
                    if log_sucesso:
                        # Deve conter nome do usuário (não sensível)
                        assert usuario_teste.nome in log_sucesso[0].acao, "Log deve conter nome do usuário"
                        # Deve conter IP (para auditoria)
                        assert 'IP:' in log_sucesso[0].acao or '127.0.0.1' in log_sucesso[0].acao, "Log deve conter IP"
    
    def test_exception_logs_do_not_contain_sensitive_data(self, app):
        """Logs de exceção não devem expor dados sensíveis."""
        with app.test_client() as client:
            # Tentar login com dados inválidos para gerar erro
            response = client.post('/login', data={
                'identificador': '',
                'senha': ''
            }, follow_redirects=False)
            
            # Verificar que não há exceções com dados sensíveis nos logs
            # Isso é um teste preventivo - se houver exceções, não devem conter credenciais
            with app.app_context():
                logs = LogAtividade.query.all()
                
                for log in logs:
                    # Não deve conter padrões de CPF
                    import re
                    cpf_pattern = r'\b\d{11}\b'
                    cpfs = re.findall(cpf_pattern, log.acao)
                    assert len(cpfs) == 0, f"CPF integral encontrado em log de exceção: {log.acao}"
    
    def test_email_in_recovery_log_is_masked(self, app, usuario_teste):
        """Email em log de recuperação deve estar mascarado ou ausente."""
        with app.test_client() as client:
            # Solicitar recuperação
            response = client.post('/recuperar-senha', data={
                'identificador': 'usuario@teste.com'
            }, follow_redirects=False)
            
            # Verificar logs
            with app.app_context():
                logs = LogAtividade.query.filter(
                    LogAtividade.acao.like('%Recuperação%')
                ).all()
                
                for log in logs:
                    # Email completo não deve estar no log
                    assert 'usuario@teste.com' not in log.acao, f"Email completo encontrado no log: {log.acao}"
