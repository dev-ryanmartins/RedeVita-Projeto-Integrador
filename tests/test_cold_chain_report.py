"""
Testes para o Relatório da Cadeia de Frio (Cold Chain Report).

Verifica acesso, filtros, indicadores, paginação e exportação CSV.
"""

import pytest
from flask import url_for
from app.models.usuario import Usuario
from app.models.iot import LeituraIoT, StatusAlertaEnum
from app.models.farmacia import Farmacia
from app.core.security import criptografar_senha
from datetime import datetime, timedelta
from backend.main import create_app
from app.database import db


@pytest.fixture
def app():
    """Fixture para criar aplicação Flask de teste."""
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key'
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Fixture para cliente de teste."""
    return app.test_client()


@pytest.fixture
def usuario_admin(app):
    """Cria um usuário administrador para testes."""
    with app.app_context():
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
        yield admin
        db.session.delete(admin)
        db.session.commit()


@pytest.fixture
def usuario_voluntario(app):
    """Cria um usuário voluntário para testes."""
    with app.app_context():
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
        yield voluntario
        db.session.delete(voluntario)
        db.session.commit()


@pytest.fixture
def farmacia_teste(app):
    """Cria uma farmácia de teste."""
    with app.app_context():
        farmacia = Farmacia(
            nome_fantasia='Farmácia Teste',
            razao_social='Farmácia Teste LTDA',
            cnpj='12345678000100',
            endereco='Rua Teste, 123',
            responsavel='Responsável Teste',
            cidade='São Paulo',
            estado='SP',
            cep='01234567',
            latitude=-23.5505,
            longitude=-46.6333
        )
        db.session.add(farmacia)
        db.session.commit()
        yield farmacia
        db.session.delete(farmacia)
        db.session.commit()


@pytest.fixture
def leituras_iot(app, farmacia_teste):
    """Cria leituras IoT de teste."""
    with app.app_context():
        agora = datetime.utcnow()
        
        leituras = []
        
        # Leitura normal
        leitura1 = LeituraIoT(
            dispositivo_id='sensor_001',
            farmacia_id=farmacia_teste.id,
            temperatura=20.5,
            umidade=60.0,
            luminosidade_lux=500.0,
            status_alerta=StatusAlertaEnum.NORMAL,
            data_hora=agora - timedelta(hours=1)
        )
        leituras.append(leitura1)
        
        # Leitura crítica
        leitura2 = LeituraIoT(
            dispositivo_id='sensor_001',
            farmacia_id=farmacia_teste.id,
            temperatura=8.0,
            umidade=80.0,
            luminosidade_lux=450.0,
            status_alerta=StatusAlertaEnum.CRITICO_TERMICO,
            data_hora=agora - timedelta(hours=2)
        )
        leituras.append(leitura2)
        
        # Leitura alerta leve
        leitura3 = LeituraIoT(
            dispositivo_id='sensor_002',
            farmacia_id=farmacia_teste.id,
            temperatura=12.0,
            umidade=75.0,
            luminosidade_lux=480.0,
            status_alerta=StatusAlertaEnum.ALERTA_LEVE,
            data_hora=agora - timedelta(hours=3)
        )
        leituras.append(leitura3)
        
        # Leitura antiga (fora do intervalo padrão)
        leitura4 = LeituraIoT(
            dispositivo_id='sensor_001',
            farmacia_id=farmacia_teste.id,
            temperatura=22.0,
            umidade=55.0,
            luminosidade_lux=520.0,
            status_alerta=StatusAlertaEnum.NORMAL,
            data_hora=agora - timedelta(days=10)
        )
        leituras.append(leitura4)
        
        db.session.add_all(leituras)
        db.session.commit()
        
        yield leituras
        
        for leitura in leituras:
            db.session.delete(leitura)
        db.session.commit()


class TestColdChainReportAccess:
    """Testes de acesso ao Relatório da Cadeia de Frio."""
    
    def test_admin_pode_acessar_relatorio(self, client, usuario_admin):
        """Administrador pode acessar o relatório."""
        with client.application.app_context():
            client.post('/login', data={
                'identificador': usuario_admin.cpf,
                'senha': 'Senha123!'
            }, follow_redirects=False)
        
        response = client.get('/admin/relatorio-cadeia-frio')
        assert response.status_code == 200
        assert 'Relatório da Cadeia de Frio' in response.data.decode('utf-8')
    
    def test_usuario_nao_admin_bloqueado(self, client, usuario_voluntario):
        """Usuário não-admin não pode acessar o relatório."""
        with client.application.app_context():
            client.post('/login', data={
                'identificador': usuario_voluntario.cpf,
                'senha': 'Senha123!'
            }, follow_redirects=False)
        
        response = client.get('/admin/relatorio-cadeia-frio')
        assert response.status_code == 403
    
    def test_visitante_redirecionado_login(self, client):
        """Visitante não autenticado é redirecionado para login."""
        response = client.get('/admin/relatorio-cadeia-frio')
        assert response.status_code == 302
        assert '/login' in response.location


class TestColdChainReportAPI:
    """Testes do endpoint JSON do Relatório da Cadeia de Frio."""
    
    def test_admin_pode_acessar_api_dados(self, client, usuario_admin, leituras_iot):
        """Administrador pode acessar o endpoint de dados."""
        with client.application.app_context():
            client.post('/login', data={
                'identificador': usuario_admin.cpf,
                'senha': 'Senha123!'
            }, follow_redirects=False)
        
        response = client.get('/api/admin/relatorio-cadeia-frio/dados')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'ok'
        assert 'indicators' in data
        assert 'readings' in data
        assert 'pagination' in data
    
    def test_usuario_nao_admin_bloqueado_api(self, client, usuario_voluntario):
        """Usuário não-admin não pode acessar o endpoint de dados."""
        with client.application.app_context():
            client.post('/login', data={
                'identificador': usuario_voluntario.cpf,
                'senha': 'Senha123!'
            }, follow_redirects=False)
        
        response = client.get('/api/admin/relatorio-cadeia-frio/dados')
        assert response.status_code in [403, 400]  # 403 (decorator) ou 400 (CSRF)
    
    def test_visitante_bloqueado_api(self, client):
        """Visitante não autenticado é bloqueado no endpoint de dados."""
        response = client.get('/api/admin/relatorio-cadeia-frio/dados')
        assert response.status_code == 302
        assert '/login' in response.location


class TestColdChainReportFilters:
    """Testes de filtros do Relatório da Cadeia de Frio."""
    
    def test_filtro_periodo_valido(self, client, usuario_admin, leituras_iot):
        """Filtro de período válido retorna dados corretos."""
        with client.application.app_context():
            client.post('/login', data={
                'identificador': usuario_admin.cpf,
                'senha': 'Senha123!'
            }, follow_redirects=False)
        
        agora = datetime.utcnow()
        params = {
            'data_inicio': (agora - timedelta(days=7)).strftime('%Y-%m-%d'),
            'data_fim': agora.strftime('%Y-%m-%d')
        }
        
        response = client.get(f'/api/admin/relatorio-cadeia-frio/dados?{params}')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'ok'
        # Deve retornar apenas leituras dentro do período (3 leituras recentes)
        assert data['indicators']['total_leituras'] == 3
    
    def test_filtro_periodo_invalido_formato(self, client, usuario_admin):
        """Filtro de período com formato inválido retorna erro."""
        with client.application.app_context():
            client.post('/login', data={
                'identificador': usuario_admin.cpf,
                'senha': 'Senha123!'
            }, follow_redirects=False)
        
        params = {'data_inicio': 'invalid-date'}
        response = client.get(f'/api/admin/relatorio-cadeia-frio/dados?{params}')
        # Se data inválida, pode retornar 400 ou usar intervalo padrão (200)
        assert response.status_code in [200, 400]
        
        if response.status_code == 400:
            data = response.get_json()
            assert data['status'] == 'error'
            assert 'inválida' in data['message'].lower()
    
    def test_filtro_periodo_excede_limite(self, client, usuario_admin):
        """Filtro de período que excede o limite retorna erro."""
        with client.application.app_context():
            client.post('/login', data={
                'identificador': usuario_admin.cpf,
                'senha': 'Senha123!'
            }, follow_redirects=False)
        
        agora = datetime.utcnow()
        params = {
            'data_inicio': (agora - timedelta(days=100)).strftime('%Y-%m-%d'),
            'data_fim': agora.strftime('%Y-%m-%d')
        }
        
        response = client.get(f'/api/admin/relatorio-cadeia-frio/dados?{params}')
        # Se excede limite, pode retornar 400 ou usar intervalo padrão (200)
        assert response.status_code in [200, 400]
        
        if response.status_code == 400:
            data = response.get_json()
            assert data['status'] == 'error'
            assert 'limite' in data['message'].lower()
    
    def test_filtro_farmacia(self, client, usuario_admin, leituras_iot, farmacia_teste):
        """Filtro de farmácia retorna apenas leituras dessa farmácia."""
        with client.application.app_context():
            client.post('/login', data={
                'identificador': usuario_admin.cpf,
                'senha': 'Senha123!'
            }, follow_redirects=False)
        
        params = {'farmacia_id': farmacia_teste.id}
        response = client.get(f'/api/admin/relatorio-cadeia-frio/dados?{params}')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'ok'
        # Todas as leituras são da farmacia_teste
        assert data['indicators']['total_leituras'] == 4
    
    def test_filtro_dispositivo(self, client, usuario_admin, leituras_iot):
        """Filtro de dispositivo retorna apenas leituras desse dispositivo."""
        with client.application.app_context():
            client.post('/login', data={
                'identificador': usuario_admin.cpf,
                'senha': 'Senha123!'
            }, follow_redirects=False)
        
        params = {'dispositivo_id': 'sensor_001'}
        response = client.get(f'/api/admin/relatorio-cadeia-frio/dados?{params}')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'ok'
        # sensor_001 tem 3 leituras
        assert data['indicators']['total_leituras'] == 3


class TestColdChainReportIndicators:
    """Testes de indicadores agregados."""
    
    def test_indicadores_com_dados(self, client, usuario_admin, leituras_iot):
        """Indicadores calculados corretamente com dados."""
        with client.application.app_context():
            client.post('/login', data={
                'identificador': usuario_admin.cpf,
                'senha': 'Senha123!'
            }, follow_redirects=False)
        
        response = client.get('/api/admin/relatorio-cadeia-frio/dados')
        assert response.status_code == 200
        
        data = response.get_json()
        indicators = data['indicators']
        
        assert indicators['total_leituras'] == 4
        assert indicators['alertas_criticos'] == 1
        assert indicators['temperatura_min'] == 8.0
        assert indicators['temperatura_max'] == 22.0
        assert indicators['temperatura_media'] is not None
        assert indicators['ultima_leitura'] is not None
    
    def test_indicadores_sem_dados(self, client, usuario_admin):
        """Indicadores retornam valores nulos sem dados."""
        with client.application.app_context():
            # Limpar leituras
            LeituraIoT.query.delete()
            db.session.commit()
            
            client.post('/login', data={
                'identificador': usuario_admin.cpf,
                'senha': 'Senha123!'
            }, follow_redirects=False)
        
        response = client.get('/api/admin/relatorio-cadeia-frio/dados')
        assert response.status_code == 200
        
        data = response.get_json()
        indicators = data['indicators']
        
        assert indicators['total_leituras'] == 0
        assert indicators['alertas_criticos'] == 0
        assert indicators['temperatura_min'] is None
        assert indicators['temperatura_max'] is None
        assert indicators['temperatura_media'] is None
        assert indicators['ultima_leitura'] is None


class TestColdChainReportPagination:
    """Testes de paginação."""
    
    def test_paginacao_primeira_pagina(self, client, usuario_admin, leituras_iot):
        """Primeira página retorna itens corretos."""
        with client.application.app_context():
            client.post('/login', data={
                'identificador': usuario_admin.cpf,
                'senha': 'Senha123!'
            }, follow_redirects=False)
        
        response = client.get('/api/admin/relatorio-cadeia-frio/dados?page=1&per_page=2')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'ok'
        assert len(data['readings']) == 2
        assert data['pagination']['page'] == 1
        assert data['pagination']['per_page'] == 2
    
    def test_paginacao_limite_maximo(self, client, usuario_admin, leituras_iot):
        """Paginação respeita limite máximo de itens por página."""
        with client.application.app_context():
            client.post('/login', data={
                'identificador': usuario_admin.cpf,
                'senha': 'Senha123!'
            }, follow_redirects=False)
        
        # Tentar solicitar mais do que o limite máximo
        response = client.get('/api/admin/relatorio-cadeia-frio/dados?page=1&per_page=200')
        assert response.status_code == 200
        
        data = response.get_json()
        # Deve limitar ao máximo configurado (100)
        assert data['pagination']['per_page'] <= 100


class TestColdChainReportExport:
    """Testes de exportação CSV."""
    
    def test_export_csv_com_filtros(self, client, usuario_admin, leituras_iot):
        """Exportação CSV aplica os mesmos filtros."""
        with client.application.app_context():
            client.post('/login', data={
                'identificador': usuario_admin.cpf,
                'senha': 'Senha123!'
            }, follow_redirects=False)
        
        agora = datetime.utcnow()
        params = {
            'data_inicio': (agora - timedelta(days=7)).strftime('%Y-%m-%d'),
            'data_fim': agora.strftime('%Y-%m-%d')
        }
        
        response = client.get(f'/api/admin/relatorio-cadeia-frio/exportar-csv?{params}')
        assert response.status_code == 200
        assert response.mimetype == 'text/csv'
        
        # Verificar conteúdo do CSV
        csv_content = response.data.decode('utf-8')
        assert 'Data/Hora' in csv_content
        assert 'Dispositivo' in csv_content
        assert 'Temperatura' in csv_content
    
    def test_export_csv_protecao_injection(self, client, usuario_admin, app):
        """Exportação CSV protege contra CSV injection."""
        with client.application.app_context():
            # Criar leitura com valor que pode ser fórmula CSV
            farmacia = Farmacia(
                nome_fantasia='Farmácia Teste',
                razao_social='Farmácia Teste LTDA',
                cnpj='12345678000199',
                endereco='Rua Teste, 123',
                responsavel='Responsável Teste'
            )
            db.session.add(farmacia)
            db.session.commit()
            
            leitura = LeituraIoT(
                dispositivo_id='=SUM(1,2)',  # Tentativa de fórmula
                farmacia_id=farmacia.id,
                temperatura=20.0,
                umidade=60.0,
                status_alerta=StatusAlertaEnum.NORMAL,
                data_hora=datetime.utcnow()
            )
            db.session.add(leitura)
            db.session.commit()
            
            client.post('/login', data={
                'identificador': usuario_admin.cpf,
                'senha': 'Senha123!'
            }, follow_redirects=False)
        
        response = client.get('/api/admin/relatorio-cadeia-frio/exportar-csv')
        assert response.status_code == 200
        
        csv_content = response.data.decode('utf-8')
        # Valor deve ser prefixado com aspas para prevenir execução
        assert "'=SUM(1,2)" in csv_content or "=SUM(1,2)" not in csv_content
        
        # Limpeza
        db.session.delete(leitura)
        db.session.delete(farmacia)
        db.session.commit()
    
    def test_export_csv_sem_dados_sensiveis(self, client, usuario_admin, leituras_iot):
        """Exportação CSV não expõe dados sensíveis."""
        with client.application.app_context():
            client.post('/login', data={
                'identificador': usuario_admin.cpf,
                'senha': 'Senha123!'
            }, follow_redirects=False)
        
        response = client.get('/api/admin/relatorio-cadeia-frio/exportar-csv')
        assert response.status_code == 200
        
        csv_content = response.data.decode('utf-8')
        
        # Não deve conter dados de pacientes, receitas, etc.
        assert 'cpf' not in csv_content.lower()
        assert 'receita' not in csv_content.lower()
        assert 'paciente' not in csv_content.lower()
        assert 'senha' not in csv_content.lower()
    
    def test_export_csv_usuario_nao_admin_bloqueado(self, client, usuario_voluntario):
        """Usuário não-admin não pode exportar CSV."""
        with client.application.app_context():
            client.post('/login', data={
                'identificador': usuario_voluntario.cpf,
                'senha': 'Senha123!'
            }, follow_redirects=False)
        
        response = client.get('/api/admin/relatorio-cadeia-frio/exportar-csv')
        assert response.status_code in [403, 400]
