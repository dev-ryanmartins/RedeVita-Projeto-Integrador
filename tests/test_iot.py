"""
IoT Tests - Testes Unitários e de Integração para Módulo IoT
Testa regras térmicas ANVISA, telemetria e autenticação RFID
Disciplina: ADS - Módulo 4 - Internet das Coisas e Hardware Virtual
"""

import pytest
from datetime import datetime, timedelta

from backend.main import create_app
from app.database import db
from app.models.farmacia import Farmacia
from app.models.iot import LeituraIoT, StatusAlertaEnum, TagRFID
from app.models.usuario import Usuario


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
def usuario_teste(app):
    """Fixture para criar usuário de teste."""
    with app.app_context():
        from app.core.security import criptografar_senha
        usuario = Usuario(
            nome='Farmacêutico Teste',
            cpf='12345678901',
            email='farmaceutico@teste.com',
            senha=criptografar_senha('senha123'),
            cargo='Farmacêutico',
            ativo=True
        )
        db.session.add(usuario)
        db.session.commit()
        yield usuario


@pytest.fixture
def usuario_admin(app):
    """Fixture para criar usuário admin de teste."""
    with app.app_context():
        from app.core.security import criptografar_senha
        usuario = Usuario(
            nome='Admin Teste',
            cpf='98765432100',
            email='admin@teste.com',
            senha=criptografar_senha('admin123'),
            cargo='Admin',
            ativo=True
        )
        db.session.add(usuario)
        db.session.commit()
        yield usuario


@pytest.fixture
def farmacia_teste(app):
    """Fixture para criar farmácia de teste."""
    with app.app_context():
        farmacia = Farmacia(
            nome_fantasia='Farmácia Teste',
            cnpj='12345678000100',
            endereco='Rua Teste, 123',
            responsavel='Dr. Teste',
            latitude=-23.5505,
            longitude=-46.6333
        )
        db.session.add(farmacia)
        db.session.commit()
        yield farmacia


# ============================================================================
# TESTES UNITÁRIOS - REGRAS TÉRMICAS ANVISA
# ============================================================================

class TestRegrasTermicas:
    """Testes para cálculo de regras térmicas conforme ANVISA."""
    
    def test_status_normal_faixa_segura(self, app):
        """Testa status NORMAL para temperatura na faixa segura."""
        with app.app_context():
            # Faixa segura: 15°C <= Temp <= 25°C e Umidade <= 70%
            leitura = LeituraIoT(
                dispositivo_id='SENSOR-001',
                temperatura=20.0,
                umidade=50.0
            )
            db.session.add(leitura)
            db.session.commit()
            
            assert leitura.status_alerta == StatusAlertaEnum.NORMAL
    
    def test_status_alerta_leve_temp_baixa(self, app):
        """Testa status ALERTA_LEVE para temperatura baixa."""
        with app.app_context():
            # Alerta: 10.0°C <= Temp < 15.0°C
            leitura = LeituraIoT(
                dispositivo_id='SENSOR-002',
                temperatura=12.0,
                umidade=60.0
            )
            db.session.add(leitura)
            db.session.commit()
            
            assert leitura.status_alerta == StatusAlertaEnum.ALERTA_LEVE
    
    def test_status_alerta_leve_temp_alta(self, app):
        """Testa status ALERTA_LEVE para temperatura alta."""
        with app.app_context():
            # Alerta: 25.0°C < Temp <= 30.0°C
            leitura = LeituraIoT(
                dispositivo_id='SENSOR-003',
                temperatura=27.0,
                umidade=65.0
            )
            db.session.add(leitura)
            db.session.commit()
            
            assert leitura.status_alerta == StatusAlertaEnum.ALERTA_LEVE
    
    def test_status_critico_temp_muito_baixa(self, app):
        """Testa status CRITICO_TERMICO para temperatura muito baixa."""
        with app.app_context():
            # Crítico: Temp < 10.0°C
            leitura = LeituraIoT(
                dispositivo_id='SENSOR-004',
                temperatura=5.0,
                umidade=70.0
            )
            db.session.add(leitura)
            db.session.commit()
            
            assert leitura.status_alerta == StatusAlertaEnum.CRITICO_TERMICO
    
    def test_status_critico_temp_muito_alta(self, app):
        """Testa status CRITICO_TERMICO para temperatura muito alta."""
        with app.app_context():
            # Crítico: Temp > 30.0°C
            leitura = LeituraIoT(
                dispositivo_id='SENSOR-005',
                temperatura=35.0,
                umidade=75.0
            )
            db.session.add(leitura)
            db.session.commit()
            
            assert leitura.status_alerta == StatusAlertaEnum.CRITICO_TERMICO
    
    def test_status_normal_umidade_alta(self, app):
        """Testa que umidade alta não afeta status se temperatura está ok."""
        with app.app_context():
            # Temperatura ok, umidade acima de 70% deve ser ALERTA
            leitura = LeituraIoT(
                dispositivo_id='SENSOR-006',
                temperatura=20.0,
                umidade=80.0
            )
            db.session.add(leitura)
            db.session.commit()
            
            # Regra: Umidade <= 70% para NORMAL
            # Se umidade > 70%, deve ser ALERTA_LEVE
            assert leitura.status_alerta == StatusAlertaEnum.ALERTA_LEVE
    
    def test_limite_inferior_normal(self, app):
        """Testa limite inferior de temperatura NORMAL (15.0°C)."""
        with app.app_context():
            leitura = LeituraIoT(
                dispositivo_id='SENSOR-007',
                temperatura=15.0,
                umidade=60.0
            )
            db.session.add(leitura)
            db.session.commit()
            
            assert leitura.status_alerta == StatusAlertaEnum.NORMAL
    
    def test_limite_superior_normal(self, app):
        """Testa limite superior de temperatura NORMAL (25.0°C)."""
        with app.app_context():
            leitura = LeituraIoT(
                dispositivo_id='SENSOR-008',
                temperatura=25.0,
                umidade=60.0
            )
            db.session.add(leitura)
            db.session.commit()
            
            assert leitura.status_alerta == StatusAlertaEnum.NORMAL


# ============================================================================
# TESTES DE INTEGRAÇÃO - API TELEMETRIA
# ============================================================================

class TestAPITelemetria:
    """Testes de integração para endpoint de telemetria."""
    
    def test_post_telemetria_sucesso(self, client, farmacia_teste):
        """Testa POST /api/iot/telemetria com dados válidos."""
        payload = {
            'dispositivo_id': 'ESP32-TEST-001',
            'temperatura': 20.5,
            'umidade': 55.0,
            'farmacia_id': farmacia_teste.id
        }
        
        response = client.post('/api/iot/telemetria', json=payload)
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['temperatura'] == 20.5
        assert data['data']['status_alerta'] == 'NORMAL'
    
    def test_post_telemetria_sem_farmacia(self, client):
        """Testa POST /api/iot/telemetria sem farmacia_id."""
        payload = {
            'dispositivo_id': 'ESP32-TEST-002',
            'temperatura': 18.0,
            'umidade': 60.0
        }
        
        response = client.post('/api/iot/telemetria', json=payload)
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
    
    def test_post_telemetria_campos_obrigatorios(self, client):
        """Testa validação de campos obrigatórios."""
        # Sem dispositivo_id
        response = client.post('/api/iot/telemetria', json={
            'temperatura': 20.0,
            'umidade': 50.0
        })
        assert response.status_code == 400
        
        # Sem temperatura
        response = client.post('/api/iot/telemetria', json={
            'dispositivo_id': 'SENSOR-001',
            'umidade': 50.0
        })
        assert response.status_code == 400
        
        # Sem umidade
        response = client.post('/api/iot/telemetria', json={
            'dispositivo_id': 'SENSOR-001',
            'temperatura': 20.0
        })
        assert response.status_code == 400
    
    def test_post_telemetria_valores_invalidos(self, client):
        """Testa validação de faixas de valores."""
        # Temperatura fora de faixa
        response = client.post('/api/iot/telemetria', json={
            'dispositivo_id': 'SENSOR-001',
            'temperatura': 150.0,  # Acima de 100°C
            'umidade': 50.0
        })
        assert response.status_code == 400
        
        # Umidade fora de faixa
        response = client.post('/api/iot/telemetria', json={
            'dispositivo_id': 'SENSOR-001',
            'temperatura': 20.0,
            'umidade': 150.0  # Acima de 100%
        })
        assert response.status_code == 400
    
    def test_post_telemetria_alerta_critico(self, client):
        """Testa geração de alerta crítico."""
        payload = {
            'dispositivo_id': 'ESP32-TEST-003',
            'temperatura': 35.0,  # Acima de 30°C - CRÍTICO
            'umidade': 80.0
        }
        
        response = client.post('/api/iot/telemetria', json=payload)
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['status_alerta'] == 'CRITICO_TERMICO'
        assert data['data']['alerta_critico'] is True
    
    def test_get_telemetria_atual(self, client, app, usuario_admin):
        """Testa GET /api/iot/telemetria/atual."""
        with app.app_context():
            # Cria leitura de teste
            leitura = LeituraIoT(
                dispositivo_id='SENSOR-001',
                temperatura=22.0,
                umidade=55.0,
                status_alerta=StatusAlertaEnum.NORMAL
            )
            db.session.add(leitura)
            db.session.commit()
        
        login_response = client.post(
            '/api/auth/login',
            json={'cpf': '98765432100', 'senha': 'admin123'},
        )
        assert login_response.status_code == 200
        response = client.get('/api/iot/telemetria/atual')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['ultima_leitura'] is not None
        assert data['data']['status_geral'] == 'NORMAL'


# ============================================================================
# TESTES DE INTEGRAÇÃO - AUTENTICAÇÃO RFID
# ============================================================================

class TestAutenticacaoRFID:
    """Testes de integração para autenticação RFID."""
    
    def test_rfid_autenticar_sucesso_farmaceutico(self, client, app, usuario_teste):
        """Testa autenticação RFID bem-sucedida com farmacêutico."""
        with app.app_context():
            # Cria tag RFID para o farmacêutico
            tag = TagRFID(
                tag_uid='a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6',
                usuario_id=usuario_teste.id,
                descricao='Crachá Farmacêutico',
                ativo=True
            )
            db.session.add(tag)
            db.session.commit()
        
        payload = {
            'tag_uid': 'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6',
            'armario_id': 'CONTROLADOS'
        }
        
        response = client.post('/api/iot/rfid-autenticar', json=payload)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['autorizado'] is True
        assert data['data']['usuario']['nome'] == 'Farmacêutico Teste'
        assert data['data']['usuario']['cargo'] == 'Farmacêutico'
    
    def test_rfid_autenticar_sucesso_admin(self, client, app, usuario_admin):
        """Testa autenticação RFID bem-sucedida com admin."""
        with app.app_context():
            # Cria tag RFID para o admin
            tag = TagRFID(
                tag_uid='z1y2x3w4v5u6t7s8r9q0p1o2n3m4l5k6j7i8h9g0f1e2d3c4b5a6',
                usuario_id=usuario_admin.id,
                descricao='Crachá Admin',
                ativo=True
            )
            db.session.add(tag)
            db.session.commit()
        
        payload = {
            'tag_uid': 'z1y2x3w4v5u6t7s8r9q0p1o2n3m4l5k6j7i8h9g0f1e2d3c4b5a6',
            'armario_id': 'CONTROLADOS'
        }
        
        response = client.post('/api/iot/rfid-autenticar', json=payload)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['autorizado'] is True
    
    def test_rfid_autenticar_tag_nao_cadastrada(self, client):
        """Testa falha com tag não cadastrada."""
        payload = {
            'tag_uid': 'tag_inexistente123456789',
            'armario_id': 'CONTROLADOS'
        }
        
        response = client.post('/api/iot/rfid-autenticar', json=payload)
        
        assert response.status_code == 403
        data = response.get_json()
        assert data['success'] is False
        assert 'Tag não reconhecida' in data['message']
    
    def test_rfid_autenticar_tag_desativada(self, client, app, usuario_teste):
        """Testa falha com tag desativada."""
        with app.app_context():
            # Cria tag RFID desativada
            tag = TagRFID(
                tag_uid='tag_desativada123456789',
                usuario_id=usuario_teste.id,
                descricao='Crachá Desativado',
                ativo=False
            )
            db.session.add(tag)
            db.session.commit()
        
        payload = {
            'tag_uid': 'tag_desativada123456789',
            'armario_id': 'CONTROLADOS'
        }
        
        response = client.post('/api/iot/rfid-autenticar', json=payload)
        
        assert response.status_code == 403
        data = response.get_json()
        assert data['success'] is False
        assert 'Tag desativada' in data['message']
    
    def test_rfid_autenticar_sem_privilegios(self, client, app):
        """Testa falha com usuário sem privilégios (paciente)."""
        with app.app_context():
            from app.core.security import criptografar_senha
            # Cria usuário paciente
            paciente = Usuario(
                nome='Paciente Teste',
                cpf='11122233344',
                email='paciente@teste.com',
                senha=criptografar_senha('senha123'),
                cargo='Paciente',
                ativo=True
            )
            db.session.add(paciente)
            db.session.commit()
            
            # Cria tag RFID para o paciente
            tag = TagRFID(
                tag_uid='tag_paciente123456789',
                usuario_id=paciente.id,
                descricao='Crachá Paciente',
                ativo=True
            )
            db.session.add(tag)
            db.session.commit()
        
        payload = {
            'tag_uid': 'tag_paciente123456789',
            'armario_id': 'CONTROLADOS'
        }
        
        response = client.post('/api/iot/rfid-autenticar', json=payload)
        
        assert response.status_code == 403
        data = response.get_json()
        assert data['success'] is False
        assert 'Privilégios insuficientes' in data['message']
    
    def test_rfid_autenticar_atualiza_ultimo_acesso(self, client, app, usuario_teste):
        """Testa que autenticação atualiza último acesso da tag."""
        with app.app_context():
            # Cria tag RFID
            tag = TagRFID(
                tag_uid='tag_acesso123456789',
                usuario_id=usuario_teste.id,
                descricao='Crachá Teste',
                ativo=True,
                ultimo_acesso=None
            )
            db.session.add(tag)
            db.session.commit()
            
            tag_id = tag.id
        
        payload = {
            'tag_uid': 'tag_acesso123456789',
            'armario_id': 'CONTROLADOS'
        }
        
        response = client.post('/api/iot/rfid-autenticar', json=payload)
        
        assert response.status_code == 200
        
        with app.app_context():
            tag_atualizada = TagRFID.query.get(tag_id)
            assert tag_atualizada.ultimo_acesso is not None
            assert isinstance(tag_atualizada.ultimo_acesso, datetime)


# ============================================================================
# TESTES DE MODELO
# ============================================================================

class TestModelosIoT:
    """Testes para modelos IoT."""
    
    def test_leitura_iot_to_dict(self, app):
        """Testa método to_dict de LeituraIoT."""
        with app.app_context():
            leitura = LeituraIoT(
                dispositivo_id='SENSOR-001',
                temperatura=20.0,
                umidade=55.0,
                status_alerta=StatusAlertaEnum.NORMAL
            )
            db.session.add(leitura)
            db.session.commit()
            
            data = leitura.to_dict()
            assert data['dispositivo_id'] == 'SENSOR-001'
            assert data['temperatura'] == 20.0
            assert data['umidade'] == 55.0
            assert data['status_alerta'] == 'NORMAL'
            assert 'data_hora' in data
    
    def test_tag_rfid_to_dict(self, app, usuario_teste):
        """Testa método to_dict de TagRFID."""
        with app.app_context():
            tag = TagRFID(
                tag_uid='tag_teste123456789',
                usuario_id=usuario_teste.id,
                descricao='Crachá Teste',
                ativo=True
            )
            db.session.add(tag)
            db.session.commit()
            
            data = tag.to_dict()
            assert data['tag_uid'] == 'tag_teste123456789'
            assert data['usuario_id'] == usuario_teste.id
            assert data['descricao'] == 'Crachá Teste'
            assert data['ativo'] is True
            assert 'data_cadastro' in data
    
    def test_relacao_tag_usuario(self, app, usuario_teste):
        """Testa relacionamento entre TagRFID e Usuario."""
        with app.app_context():
            tag = TagRFID(
                tag_uid='tag_relacao123456789',
                usuario_id=usuario_teste.id,
                descricao='Crachá Relação',
                ativo=True
            )
            db.session.add(tag)
            db.session.commit()
            
            # Busca tag e verifica relacionamento
            tag_buscada = TagRFID.query.first()
            assert tag_buscada.usuario.nome == 'Farmacêutico Teste'
            assert tag_buscada.usuario.cargo == 'Farmacêutico'
    
    def test_relacao_leitura_farmacia(self, app, farmacia_teste):
        """Testa relacionamento entre LeituraIoT e Farmacia."""
        with app.app_context():
            leitura = LeituraIoT(
                dispositivo_id='SENSOR-001',
                farmacia_id=farmacia_teste.id,
                temperatura=20.0,
                umidade=55.0
            )
            db.session.add(leitura)
            db.session.commit()
            
            # Busca leitura e verifica relacionamento
            leitura_buscada = LeituraIoT.query.first()
            assert leitura_buscada.farmacia.nome_fantasia == 'Farmácia Teste'
