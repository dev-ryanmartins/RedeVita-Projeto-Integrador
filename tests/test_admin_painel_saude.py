"""
Testes para o Painel de Saúde Operacional (Admin Health Dashboard).

Verifica que o painel é acessível apenas por administradores,
que os dados são corretos e que os estados de erro são tratados adequadamente.
"""

import pytest
from flask import url_for
from app.models.usuario import Usuario
from app.core.security import criptografar_senha
from app.models.iot import LeituraIoT, StatusAlertaEnum
from datetime import datetime, timedelta


class TestAdminPainelSaudeAccess:
    """Testes de acesso ao Painel de Saúde Operacional."""
    
    def test_admin_pode_acessar_painel(self, client, usuario_admin):
        """Administrador pode acessar o painel de saúde."""
        with client.application.app_context():
            login_response = client.post('/login', data={
                'identificador': usuario_admin.cpf,
                'senha': 'Senha123!'
            }, follow_redirects=False)
        
        response = client.get('/admin/painel-saude')
        assert response.status_code == 200
        assert b'Painel de Saúde Operacional' in response.data
    
    def test_usuario_nao_admin_bloqueado(self, client, usuario_voluntario):
        """Usuário não-admin não pode acessar o painel de saúde."""
        with client.application.app_context():
            login_response = client.post('/login', data={
                'identificador': usuario_voluntario.cpf,
                'senha': 'Senha123!'
            }, follow_redirects=False)
        
        response = client.get('/admin/painel-saude')
        assert response.status_code == 403
    
    def test_visitante_redirecionado_login(self, client):
        """Visitante não autenticado é redirecionado para login."""
        response = client.get('/admin/painel-saude')
        assert response.status_code == 302
        assert '/login' in response.location


class TestAdminPainelSaudeAPI:
    """Testes do endpoint JSON do Painel de Saúde Operacional."""
    
    def test_admin_pode_acessar_api_dados(self, client, usuario_admin):
        """Administrador pode acessar o endpoint de dados do painel."""
        with client.application.app_context():
            client.post('/login', data={
                'identificador': usuario_admin.cpf,
                'senha': 'Senha123!'
            }, follow_redirects=False)
        
        response = client.get('/api/admin/painel-saude/dados')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'ok'
        assert 'system' in data
        assert 'iot' in data
        assert 'timestamp' in data
    
    def test_usuario_nao_admin_bloqueado_api(self, client, usuario_voluntario):
        """Usuário não-admin não pode acessar o endpoint de dados."""
        with client.application.app_context():
            client.post('/login', data={
                'identificador': usuario_voluntario.cpf,
                'senha': 'Senha123!'
            }, follow_redirects=False)
        
        response = client.get('/api/admin/painel-saude/dados')
        assert response.status_code == 403
    
    def test_visitante_bloqueado_api(self, client):
        """Visitante não autenticado é bloqueado no endpoint de dados."""
        response = client.get('/api/admin/painel-saude/dados')
        assert response.status_code == 302
        assert '/login' in response.location


class TestAdminPainelSaudeData:
    """Testes de dados retornados pelo Painel de Saúde Operacional."""
    
    def test_resposta_com_dados_sinteticos(self, client, usuario_admin, app):
        """Endpoint retorna dados sintéticos quando há dados no sistema."""
        with client.application.app_context():
            from app.database import db
            
            # Criar leituras IoT sintéticas
            farmacia_id = 1  # Assumindo que existe
            agora = datetime.utcnow()
            
            # Leitura normal
            leitura1 = LeituraIoT(
                dispositivo_id='sensor_001',
                farmacia_id=farmacia_id,
                temperatura=20.5,
                umidade=60.0,
                status_alerta=StatusAlertaEnum.NORMAL,
                data_hora=agora - timedelta(hours=1)
            )
            
            # Leitura crítica
            leitura2 = LeituraIoT(
                dispositivo_id='sensor_002',
                farmacia_id=farmacia_id,
                temperatura=8.0,
                umidade=80.0,
                status_alerta=StatusAlertaEnum.CRITICO_TERMICO,
                data_hora=agora - timedelta(hours=2)
            )
            
            db.session.add(leitura1)
            db.session.add(leitura2)
            db.session.commit()
            
            # Login
            client.post('/login', data={
                'identificador': usuario_admin.cpf,
                'senha': 'Senha123!'
            }, follow_redirects=False)
        
        response = client.get('/api/admin/painel-saude/dados')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'ok'
        assert data['iot']['leituras_24h'] >= 2
        assert data['iot']['dispositivos_24h'] >= 2
        assert data['iot']['criticas_24h'] >= 1
        assert data['iot']['estado'] in ['saudavel', 'atencao', 'desatualizado']
        assert data['iot']['ultima_leitura'] is not None
    
    def test_resposta_sem_dados_iot(self, client, usuario_admin, app):
        """Endpoint retorna estado 'sem_dados' quando não há leituras IoT."""
        with client.application.app_context():
            from app.database import db
            
            # Limpar leituras existentes
            LeituraIoT.query.delete()
            db.session.commit()
            
            # Login
            client.post('/login', data={
                'identificador': usuario_admin.cpf,
                'senha': 'Senha123!'
            }, follow_redirects=False)
        
        response = client.get('/api/admin/painel-saude/dados')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'ok'
        assert data['iot']['estado'] == 'sem_dados'
        assert data['iot']['leituras_24h'] == 0
        assert data['iot']['dispositivos_24h'] == 0
        assert data['iot']['criticas_24h'] == 0
        assert data['iot']['ultima_leitura'] is None
    
    def test_erro_banco_tratado_sem_vazar_detalhes(self, client, usuario_admin, app):
        """Erro de banco é tratado sem vazar detalhes sensíveis."""
        with client.application.app_context():
            # Login
            client.post('/login', data={
                'identificador': usuario_admin.cpf,
                'senha': 'Senha123!'
            }, follow_redirects=False)
        
        response = client.get('/api/admin/painel-saude/dados')
        # Em caso de erro real, a resposta deve ser 500 com mensagem genérica
        # e não expor detalhes de banco
        if response.status_code == 500:
            data = response.get_json()
            assert 'error' in data or 'message' in data
            # Não deve expor DSN, credenciais, ou tracebacks completos
            assert 'dsn' not in str(data).lower()
            assert 'password' not in str(data).lower()
            assert 'traceback' not in str(data).lower()


class TestAdminPainelSaudeTemplate:
    """Testes do template do Painel de Saúde Operacional."""
    
    def test_template_contem_estrutura_esperada(self, client, usuario_admin):
        """Template HTML contém a estrutura esperada do painel."""
        with client.application.app_context():
            client.post('/login', data={
                'identificador': usuario_admin.cpf,
                'senha': 'Senha123!'
            }, follow_redirects=False)
        
        response = client.get('/admin/painel-saude')
        assert response.status_code == 200
        
        # Verificar elementos principais
        assert b'Painel de Saúde Operacional' in response.data
        assert b'M\xe9tricas do Sistema' in response.data or b'Metricas do Sistema' in response.data
        assert b'Telemetria IoT' in response.data
        assert b'Status Geral' in response.data
        assert b'Uptime' in response.data
        assert b'Mem\xf3ria' in response.data or b'Memoria' in response.data
        assert b'CPU' in response.data
        assert b'Banco de Dados' in response.data
        assert b'\xdaltima Leitura' in response.data or b'Ultima Leitura' in response.data or b'Nenhuma leitura' in response.data
        assert b'Leituras (24h)' in response.data
        assert b'Dispositivos Ativos' in response.data
    
    def test_template_responsivo(self, client, usuario_admin):
        """Template inclui CSS específico do painel de saúde."""
        with client.application.app_context():
            client.post('/login', data={
                'identificador': usuario_admin.cpf,
                'senha': 'Senha123!'
            }, follow_redirects=False)
        
        response = client.get('/admin/painel-saude')
        assert response.status_code == 200
        
        # Verificar que o CSS específico foi carregado
        assert b'admin_painel_saude.css' in response.data


@pytest.fixture
def usuario_admin(app):
    """Cria um usuário administrador para testes."""
    with app.app_context():
        from app.database import db
        admin = Usuario(
            nome='Admin Teste',
            cpf='12345678901',
            email='admin@teste.local',
            senha=criptografar_senha('Senha123!'),
            cargo='Admin',
            ativo=True,
            senha_trocada=True
        )
        db.session.add(admin)
        db.session.commit()
        return admin


@pytest.fixture
def usuario_voluntario(app):
    """Cria um usuário voluntário para testes."""
    with app.app_context():
        from app.database import db
        voluntario = Usuario(
            nome='Voluntário Teste',
            cpf='98765432100',
            email='voluntario@teste.local',
            senha=criptografar_senha('Senha123!'),
            cargo='Voluntário',
            ativo=True,
            senha_trocada=True
        )
        db.session.add(voluntario)
        db.session.commit()
        return voluntario
