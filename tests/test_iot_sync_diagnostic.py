"""
Tests for IoT Sync Diagnostic
Tests for the IoT batch telemetry tracking and diagnostic page
"""
import pytest
from datetime import datetime, timedelta
from flask import url_for

from app.models.iot import LoteTelemetria, LeituraIoT, ResultadoLoteEnum, StatusAlertaEnum
from app.models.usuario import Usuario
from app.models.farmacia import Farmacia


class TestIoTSyncDiagnosticAccess:
    """Test access control for IoT sync diagnostic"""
    
    def test_admin_pode_acessar_diagnostico(self, client, admin_user):
        """Admin can access the diagnostic page"""
        with client.session_transaction() as sess:
            sess['_user_id'] = admin_user.id
            sess['_fresh'] = True
        
        response = client.get('/admin/diagnostico-iot')
        assert response.status_code == 200
        assert 'Diagnóstico de Sincronização IoT' in response.data.decode('utf-8')
    
    def test_usuario_nao_admin_bloqueado(self, client, regular_user):
        """Non-admin user is blocked from diagnostic page"""
        with client.session_transaction() as sess:
            sess['_user_id'] = regular_user.id
            sess['_fresh'] = True
        
        response = client.get('/admin/diagnostico-iot')
        assert response.status_code == 403
    
    def test_visitante_redirecionado_login(self, client):
        """Visitor is redirected to login"""
        response = client.get('/admin/diagnostico-iot')
        assert response.status_code == 302
        assert '/login' in response.location


class TestIoTSyncDiagnosticAPI:
    """Test API endpoints for IoT sync diagnostic"""
    
    def test_admin_pode_acessar_api_dados(self, client, admin_user, app):
        """Admin can access the API data endpoint"""
        with client.session_transaction() as sess:
            sess['_user_id'] = admin_user.id
            sess['_fresh'] = True
        
        with app.app_context():
            response = client.get('/api/admin/diagnostico-iot/dados')
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'ok'
            assert 'lotes' in data
            assert 'agregados' in data
    
    def test_usuario_nao_admin_bloqueado_api(self, client, regular_user):
        """Non-admin user is blocked from API endpoint"""
        with client.session_transaction() as sess:
            sess['_user_id'] = regular_user.id
            sess['_fresh'] = True
        
        response = client.get('/api/admin/diagnostico-iot/dados')
        assert response.status_code == 403
    
    def test_visitante_bloqueado_api(self, client):
        """Visitor is blocked from API endpoint"""
        response = client.get('/api/admin/diagnostico-iot/dados')
        assert response.status_code == 403


class TestLoteTelemetriaPersistence:
    """Test persistence of LoteTelemetria records"""
    
    def test_lote_completo_persistido_corretamente(self, app, db_session):
        """Complete batch is persisted correctly"""
        with app.app_context():
            lote = LoteTelemetria(
                lote_id='test-lote-001',
                data_recebimento=datetime.utcnow(),
                total_recebidas=10,
                total_processadas=10,
                total_rejeitadas=0,
                resultado=ResultadoLoteEnum.COMPLETO,
                qtd_dispositivos=1,
                dispositivo_principal='sensor_001',
                erros_por_categoria=None
            )
            db_session.add(lote)
            db_session.commit()
            
            retrieved = LoteTelemetria.query.filter_by(lote_id='test-lote-001').first()
            assert retrieved is not None
            assert retrieved.resultado == ResultadoLoteEnum.COMPLETO
            assert retrieved.total_processadas == 10
            assert retrieved.total_rejeitadas == 0
    
    def test_lote_parcial_persistido_corretamente(self, app, db_session):
        """Partial batch is persisted correctly"""
        with app.app_context():
            lote = LoteTelemetria(
                lote_id='test-lote-002',
                data_recebimento=datetime.utcnow(),
                total_recebidas=10,
                total_processadas=7,
                total_rejeitadas=3,
                resultado=ResultadoLoteEnum.PARCIAL,
                qtd_dispositivos=2,
                dispositivo_principal=None,  # Misto
                erros_por_categoria={'campos_obrigatorios': 2, 'tipos_invalidos': 1}
            )
            db_session.add(lote)
            db_session.commit()
            
            retrieved = LoteTelemetria.query.filter_by(lote_id='test-lote-002').first()
            assert retrieved is not None
            assert retrieved.resultado == ResultadoLoteEnum.PARCIAL
            assert retrieved.dispositivo_principal is None
            assert retrieved.erros_por_categoria is not None
    
    def test_lote_rejeitado_persistido_corretamente(self, app, db_session):
        """Rejected batch is persisted correctly"""
        with app.app_context():
            lote = LoteTelemetria(
                lote_id='test-lote-003',
                data_recebimento=datetime.utcnow(),
                total_recebidas=5,
                total_processadas=0,
                total_rejeitadas=5,
                resultado=ResultadoLoteEnum.REJEITADO,
                qtd_dispositivos=1,
                dispositivo_principal='sensor_002',
                erros_por_categoria={'campos_obrigatorios': 5}
            )
            db_session.add(lote)
            db_session.commit()
            
            retrieved = LoteTelemetria.query.filter_by(lote_id='test-lote-003').first()
            assert retrieved is not None
            assert retrieved.resultado == ResultadoLoteEnum.REJEITADO
            assert retrieved.total_processadas == 0
            assert retrieved.total_rejeitadas == 5
    
    def test_lote_misto_sem_dispositivo_principal(self, app, db_session):
        """Mixed batch (multiple devices) has no principal device"""
        with app.app_context():
            lote = LoteTelemetria(
                lote_id='test-lote-004',
                data_recebimento=datetime.utcnow(),
                total_recebidas=20,
                total_processadas=18,
                total_rejeitadas=2,
                resultado=ResultadoLoteEnum.PARCIAL,
                qtd_dispositivos=3,
                dispositivo_principal=None,  # Misto, não tem principal
                erros_por_categoria={'tipos_invalidos': 2}
            )
            db_session.add(lote)
            db_session.commit()
            
            retrieved = LoteTelemetria.query.filter_by(lote_id='test-lote-004').first()
            assert retrieved is not None
            assert retrieved.qtd_dispositivos == 3
            assert retrieved.dispositivo_principal is None


class TestLoteTelemetriaAPIEndpoint:
    """Test the /iot/telemetria/lote endpoint instrumentation"""
    
    def test_endpoint_registra_lote_completo(self, client, app, db_session, farmacia_teste):
        """Endpoint registers complete batch correctly"""
        payload = {
            'leituras': [
                {
                    'dispositivo_id': 'sensor_001',
                    'temperatura': 20.0,
                    'umidade': 60.0,
                    'farmacia_id': farmacia_teste.id
                },
                {
                    'dispositivo_id': 'sensor_001',
                    'temperatura': 21.0,
                    'umidade': 58.0,
                    'farmacia_id': farmacia_teste.id
                }
            ]
        }
        
        with app.app_context():
            response = client.post('/api/iot/telemetria/lote', json=payload)
            assert response.status_code == 201
            
            data = response.get_json()
            assert data['processadas'] == 2
            assert data['total_recebidas'] == 2
            
            # Verificar se o lote foi persistido
            lote = LoteTelemetria.query.order_by(LoteTelemetria.data_recebimento.desc()).first()
            assert lote is not None
            assert lote.resultado == ResultadoLoteEnum.COMPLETO
            assert lote.total_processadas == 2
            assert lote.dispositivo_principal == 'sensor_001'
    
    def test_endpoint_registra_lote_parcial(self, client, app, db_session, farmacia_teste):
        """Endpoint registers partial batch correctly"""
        payload = {
            'leituras': [
                {
                    'dispositivo_id': 'sensor_001',
                    'temperatura': 20.0,
                    'umidade': 60.0,
                    'farmacia_id': farmacia_teste.id
                },
                {
                    'dispositivo_id': 'sensor_001',
                    'temperatura': None,  # Inválido
                    'umidade': 60.0,
                    'farmacia_id': farmacia_teste.id
                }
            ]
        }
        
        with app.app_context():
            response = client.post('/api/iot/telemetria/lote', json=payload)
            assert response.status_code == 201
            
            data = response.get_json()
            assert data['processadas'] == 1
            assert data['total_recebidas'] == 2
            assert len(data['erros']) == 1
            
            # Verificar se o lote foi persistido
            lote = LoteTelemetria.query.order_by(LoteTelemetria.data_recebimento.desc()).first()
            assert lote is not None
            assert lote.resultado == ResultadoLoteEnum.PARCIAL
            assert lote.total_processadas == 1
            assert lote.total_rejeitadas == 1
            assert lote.erros_por_categoria is not None
    
    def test_endpoint_preserva_contrato_existente(self, client, app, db_session, farmacia_teste):
        """Endpoint preserves existing contract"""
        payload = {
            'leituras': [
                {
                    'dispositivo_id': 'sensor_001',
                    'temperatura': 20.0,
                    'umidade': 60.0,
                    'farmacia_id': farmacia_teste.id
                }
            ]
        }
        
        with app.app_context():
            response = client.post('/api/iot/telemetria/lote', json=payload)
            assert response.status_code == 201
            
            data = response.get_json()
            # Campos originais devem estar presentes
            assert 'processadas' in data
            assert 'total_recebidas' in data
            assert 'erros' in data
            assert 'leituras' in data
            # Nenhum campo novo deve quebrar o contrato
            assert isinstance(data['processadas'], int)
            assert isinstance(data['total_recebidas'], int)
            assert isinstance(data['erros'], list)
            assert isinstance(data['leituras'], list)


class TestIoTSyncDiagnosticFilters:
    """Test filtering in diagnostic API"""
    
    def test_filtro_periodo_valido(self, client, admin_user, app, db_session):
        """Valid period filter works correctly"""
        with client.session_transaction() as sess:
            sess['_user_id'] = admin_user.id
            sess['_fresh'] = True
        
        with app.app_context():
            # Criar lotes em datas diferentes
            hoje = datetime.utcnow()
            ontem = hoje - timedelta(days=1)
            
            lote1 = LoteTelemetria(
                lote_id='lote-hoje',
                data_recebimento=hoje,
                total_recebidas=10,
                total_processadas=10,
                total_rejeitadas=0,
                resultado=ResultadoLoteEnum.COMPLETO,
                qtd_dispositivos=1,
                dispositivo_principal='sensor_001'
            )
            lote2 = LoteTelemetria(
                lote_id='lote-ontem',
                data_recebimento=ontem,
                total_recebidas=5,
                total_processadas=5,
                total_rejeitadas=0,
                resultado=ResultadoLoteEnum.COMPLETO,
                qtd_dispositivos=1,
                dispositivo_principal='sensor_002'
            )
            db_session.add(lote1)
            db_session.add(lote2)
            db_session.commit()
            
            # Filtrar apenas por hoje
            params = {
                'data_inicio': hoje.date().isoformat(),
                'data_fim': hoje.date().isoformat()
            }
            response = client.get(f'/api/admin/diagnostico-iot/dados?{params}')
            assert response.status_code == 200
            
            data = response.get_json()
            assert len(data['lotes']) == 1
            assert data['lotes'][0]['lote_id'] == 'lote-hoje'
    
    def test_filtro_resultado(self, client, admin_user, app, db_session):
        """Result filter works correctly"""
        with client.session_transaction() as sess:
            sess['_user_id'] = admin_user.id
            sess['_fresh'] = True
        
        with app.app_context():
            hoje = datetime.utcnow()
            
            lote1 = LoteTelemetria(
                lote_id='lote-completo',
                data_recebimento=hoje,
                total_recebidas=10,
                total_processadas=10,
                total_rejeitadas=0,
                resultado=ResultadoLoteEnum.COMPLETO,
                qtd_dispositivos=1,
                dispositivo_principal='sensor_001'
            )
            lote2 = LoteTelemetria(
                lote_id='lote-parcial',
                data_recebimento=hoje,
                total_recebidas=10,
                total_processadas=7,
                total_rejeitadas=3,
                resultado=ResultadoLoteEnum.PARCIAL,
                qtd_dispositivos=1,
                dispositivo_principal='sensor_002'
            )
            db_session.add(lote1)
            db_session.add(lote2)
            db_session.commit()
            
            # Filtrar por PARCIAL
            params = {'resultado': 'PARCIAL'}
            response = client.get(f'/api/admin/diagnostico-iot/dados?{params}')
            assert response.status_code == 200
            
            data = response.get_json()
            assert len(data['lotes']) == 1
            assert data['lotes'][0]['resultado'] == 'PARCIAL'
    
    def test_filtro_dispositivo(self, client, admin_user, app, db_session):
        """Device filter works correctly (only for single-device batches)"""
        with client.session_transaction() as sess:
            sess['_user_id'] = admin_user.id
            sess['_fresh'] = True
        
        with app.app_context():
            hoje = datetime.utcnow()
            
            lote1 = LoteTelemetria(
                lote_id='lote-sensor-001',
                data_recebimento=hoje,
                total_recebidas=10,
                total_processadas=10,
                total_rejeitadas=0,
                resultado=ResultadoLoteEnum.COMPLETO,
                qtd_dispositivos=1,
                dispositivo_principal='sensor_001'
            )
            lote2 = LoteTelemetria(
                lote_id='lote-sensor-002',
                data_recebimento=hoje,
                total_recebidas=5,
                total_processadas=5,
                total_rejeitadas=0,
                resultado=ResultadoLoteEnum.COMPLETO,
                qtd_dispositivos=1,
                dispositivo_principal='sensor_002'
            )
            db_session.add(lote1)
            db_session.add(lote2)
            db_session.commit()
            
            # Filtrar por sensor_001
            params = {'dispositivo': 'sensor_001'}
            response = client.get(f'/api/admin/diagnostico-iot/dados?{params}')
            assert response.status_code == 200
            
            data = response.get_json()
            assert len(data['lotes']) == 1
            assert data['lotes'][0]['dispositivo_principal'] == 'sensor_001'
    
    def test_filtro_intervalo_excede_limite(self, client, admin_user):
        """Interval exceeding maximum is rejected"""
        with client.session_transaction() as sess:
            sess['_user_id'] = admin_user.id
            sess['_fresh'] = True
        
        # Intervalo de 100 dias (excede limite de 90)
        data_inicio = (datetime.utcnow() - timedelta(days=100)).date().isoformat()
        data_fim = datetime.utcnow().date().isoformat()
        
        params = {'data_inicio': data_inicio, 'data_fim': data_fim}
        response = client.get(f'/api/admin/diagnostico-iot/dados?{params}')
        assert response.status_code == 400
        data = response.get_json()
        assert 'intervalo máximo' in data.get('mensagem', '').lower()


class TestIoTSyncDiagnosticPagination:
    """Test pagination in diagnostic API"""
    
    def test_paginacao_primeira_pagina(self, client, admin_user, app, db_session):
        """First page of pagination works correctly"""
        with client.session_transaction() as sess:
            sess['_user_id'] = admin_user.id
            sess['_fresh'] = True
        
        with app.app_context():
            hoje = datetime.utcnow()
            
            # Criar 25 lotes
            for i in range(25):
                lote = LoteTelemetria(
                    lote_id=f'lote-{i:03d}',
                    data_recebimento=hoje,
                    total_recebidas=10,
                    total_processadas=10,
                    total_rejeitadas=0,
                    resultado=ResultadoLoteEnum.COMPLETO,
                    qtd_dispositivos=1,
                    dispositivo_principal=f'sensor_{i:03d}'
                )
                db_session.add(lote)
            db_session.commit()
            
            # Primeira página (tamanho padrão 20)
            params = {'page': 1, 'page_size': 20}
            response = client.get(f'/api/admin/diagnostico-iot/dados?{params}')
            assert response.status_code == 200
            
            data = response.get_json()
            assert len(data['lotes']) == 20
            assert data['paginacao']['page'] == 1
            assert data['paginacao']['has_next'] is True
            assert data['paginacao']['has_prev'] is False
    
    def test_paginacao_limite_maximo(self, client, admin_user, app, db_session):
        """Maximum page size limit is enforced"""
        with client.session_transaction() as sess:
            sess['_user_id'] = admin_user.id
            sess['_fresh'] = True
        
        with app.app_context():
            hoje = datetime.utcnow()
            
            # Criar 60 lotes
            for i in range(60):
                lote = LoteTelemetria(
                    lote_id=f'lote-{i:03d}',
                    data_recebimento=hoje,
                    total_recebidas=10,
                    total_processadas=10,
                    total_rejeitadas=0,
                    resultado=ResultadoLoteEnum.COMPLETO,
                    qtd_dispositivos=1,
                    dispositivo_principal=f'sensor_{i:03d}'
                )
                db_session.add(lote)
            db_session.commit()
            
            # Tentar solicitar 100 itens (limite é 50)
            params = {'page': 1, 'page_size': 100}
            response = client.get(f'/api/admin/diagnostico-iot/dados?{params}')
            assert response.status_code == 200
            
            data = response.get_json()
            # Deve retornar no máximo 50
            assert len(data['lotes']) <= 50


class TestIoTSyncDiagnosticEmptyState:
    """Test empty state handling"""
    
    def test_sem_historico_retorna_vazio(self, client, admin_user, app, db_session):
        """No history returns empty state"""
        with client.session_transaction() as sess:
            sess['_user_id'] = admin_user.id
            sess['_fresh'] = True
        
        with app.app_context():
            # Não criar nenhum lote
            response = client.get('/api/admin/diagnostico-iot/dados')
            assert response.status_code == 200
            
            data = response.get_json()
            assert data['status'] == 'ok'
            assert len(data['lotes']) == 0
            assert data['agregados']['total_lotes'] == 0
    
    def test_filtro_sem_resultados_retorna_vazio(self, client, admin_user, app, db_session):
        """Filter with no results returns empty state"""
        with client.session_transaction() as sess:
            sess['_user_id'] = admin_user.id
            sess['_fresh'] = True
        
        with app.app_context():
            hoje = datetime.utcnow()
            
            # Criar lote COMPLETO
            lote = LoteTelemetria(
                lote_id='lote-completo',
                data_recebimento=hoje,
                total_recebidas=10,
                total_processadas=10,
                total_rejeitadas=0,
                resultado=ResultadoLoteEnum.COMPLETO,
                qtd_dispositivos=1,
                dispositivo_principal='sensor_001'
            )
            db_session.add(lote)
            db_session.commit()
            
            # Filtrar por REJEITADO (não existe)
            params = {'resultado': 'REJEITADO'}
            response = client.get(f'/api/admin/diagnostico-iot/dados?{params}')
            assert response.status_code == 200
            
            data = response.get_json()
            assert len(data['lotes']) == 0


class TestIoTSyncDiagnosticDispositivos:
    """Test dispositivos endpoint"""
    
    def test_listar_dispositivos_retorna_lista(self, client, admin_user, app, db_session):
        """List devices endpoint returns device list"""
        with client.session_transaction() as sess:
            sess['_user_id'] = admin_user.id
            sess['_fresh'] = True
        
        with app.app_context():
            hoje = datetime.utcnow()
            
            # Criar lotes com dispositivos diferentes
            lote1 = LoteTelemetria(
                lote_id='lote-001',
                data_recebimento=hoje,
                total_recebidas=10,
                total_processadas=10,
                total_rejeitadas=0,
                resultado=ResultadoLoteEnum.COMPLETO,
                qtd_dispositivos=1,
                dispositivo_principal='sensor_001'
            )
            lote2 = LoteTelemetria(
                lote_id='lote-002',
                data_recebimento=hoje,
                total_recebidas=5,
                total_processadas=5,
                total_rejeitadas=0,
                resultado=ResultadoLoteEnum.COMPLETO,
                qtd_dispositivos=1,
                dispositivo_principal='sensor_002'
            )
            db_session.add(lote1)
            db_session.add(lote2)
            db_session.commit()
            
            response = client.get('/api/admin/diagnostico-iot/dispositivos')
            assert response.status_code == 200
            
            data = response.get_json()
            assert 'dispositivos' in data
            assert 'sensor_001' in data['dispositivos']
            assert 'sensor_002' in data['dispositivos']
    
    def test_listar_dispositivos_sem_lote_principal(self, client, admin_user, app, db_session):
        """List devices excludes mixed batches (no principal device)"""
        with client.session_transaction() as sess:
            sess['_user_id'] = admin_user.id
            sess['_fresh'] = True
        
        with app.app_context():
            hoje = datetime.utcnow()
            
            # Criar lote misto (sem dispositivo principal)
            lote = LoteTelemetria(
                lote_id='lote-misto',
                data_recebimento=hoje,
                total_recebidas=20,
                total_processadas=18,
                total_rejeitadas=2,
                resultado=ResultadoLoteEnum.PARCIAL,
                qtd_dispositivos=3,
                dispositivo_principal=None
            )
            db_session.add(lote)
            db_session.commit()
            
            response = client.get('/api/admin/diagnostico-iot/dispositivos')
            assert response.status_code == 200
            
            data = response.get_json()
            # Não deve incluir o lote misto
            assert len(data['dispositivos']) == 0


# Fixtures
@pytest.fixture
def admin_user(db_session):
    """Create admin user for testing"""
    user = Usuario(
        nome='Admin Test',
        email='admin@test.com',
        cargo='Admin',
        ativo=True
    )
    user.set_senha('senha123')
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def regular_user(db_session):
    """Create regular user for testing"""
    user = Usuario(
        nome='User Test',
        email='user@test.com',
        cargo='Farmacêutico',
        ativo=True
    )
    user.set_senha('senha123')
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def farmacia_teste(db_session):
    """Create test pharmacy"""
    farmacia = Farmacia(
        nome_fantasia='Farmacia Teste',
        razao_social='Farmacia Teste LTDA',
        cnpj='12345678000100',
        endereco='Rua Teste, 123',
        responsavel='Responsável Teste',
        latitude=-23.5505,
        longitude=-46.6333
    )
    db_session.add(farmacia)
    db_session.commit()
    return farmacia
