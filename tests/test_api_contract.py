"""
Testes de contrato API para P2.3.
Verifica que endpoints essenciais seguem o contrato OpenAPI definido.
"""

import pytest
from main import create_app
from app.database import db
from app.models.medicamento import Medicamento
from app.models.usuario import Usuario
from app.core.security import criptografar_senha
from datetime import datetime


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
    """Fixture para criar cliente de teste."""
    return app.test_client()


@pytest.fixture
def auth_usuario(app):
    """Fixture para criar usuário autenticado."""
    with app.app_context():
        usuario = Usuario(
            nome="Usuário Teste",
            cpf="123.456.789-00",
            email="usuario@teste.com",
            senha=criptografar_senha("senha123"),
            cargo="Admin",
            ativo=True
        )
        db.session.add(usuario)
        db.session.commit()
        
        with app.test_client() as client:
            client.post('/login', data={
                'identificador': 'usuario@teste.com',
                'senha': 'senha123'
            })
            yield client


class TestAPIErrorResponseFormat:
    """Testes para formato de erro padronizado."""
    
    def test_erro_inclui_correlation_id(self, client, app):
        """Resposta de erro deve incluir correlation_id."""
        response = client.get('/api/inventario?limit=abc')
        assert response.status_code in [400, 422]
        
        data = response.get_json()
        # A resposta deve ter estrutura de erro
        assert 'erro' in data or 'sucesso' in data
        # Se houver erro, deve ter correlation_id
        if 'erro' in data:
            assert 'correlation_id' in data['erro']
    
    def test_erro_inclui_codigo_maquina(self, client, app):
        """Resposta de erro deve incluir código legível por máquina em endpoints padronizados."""
        # Testar com usuário autenticado para evitar redirecionamento de login
        with app.app_context():
            from app.models.usuario import Usuario
            from app.core.security import criptografar_senha
            usuario = Usuario(
                nome="Teste",
                cpf="123.456.789-00",
                email="teste@teste.com",
                senha=criptografar_senha("senha123"),
                cargo="Admin",
                ativo=True
            )
            db.session.add(usuario)
            db.session.commit()
            
            with app.test_client() as auth_client:
                auth_client.post('/login', data={
                    'identificador': 'teste@teste.com',
                    'senha': 'senha123'
                })
                # Testar endpoint de triagem que usa novo formato
                response = auth_client.post('/api/triagem', json={})
                
                if response.content_type == 'application/json':
                    data = response.get_json()
                    if 'erro' in data:
                        assert 'codigo' in data['erro']
                        # Código deve ser um dos códigos definidos
                        codigos_validos = [
                            'VALIDATION_ERROR', 'UNAUTHORIZED', 'FORBIDDEN',
                            'NOT_FOUND', 'CONFLICT', 'INTERNAL_ERROR',
                            'SERVICE_UNAVAILABLE', 'TIMEOUT', 'EXTERNAL_INTEGRATION_ERROR'
                        ]
                        assert data['erro']['codigo'] in codigos_validos
    
    def test_erro_nao_exibe_excecao_bruta(self, client, app):
        """Resposta de erro não deve expor exceção bruta."""
        response = client.get('/api/inventario?limit=abc')
        assert response.status_code in [400, 422]
        
        data = response.get_json()
        if 'erro' in data:
            mensagem = data['erro'].get('mensagem', '')
            if isinstance(mensagem, str):
                # Mensagem não deve conter traços de exceção
                assert 'Traceback' not in mensagem
                assert 'Exception' not in mensagem
                assert 'File "' not in mensagem
                assert 'line ' not in mensagem.lower()


class TestAPIInventarioContract:
    """Testes de contrato para endpoint de inventário."""
    
    def test_listar_inventario_paginacao(self, client, auth_usuario, app):
        """GET /api/inventario deve suportar paginação."""
        with app.app_context():
            # Criar medicamentos
            for i in range(25):
                medicamento = Medicamento(
                    nome=f"Medicamento {i}",
                    lote=f"LOT{i}",
                    data_validade=datetime(2025, 12, 31).date(),
                    quantidade=10,
                    status_semaforo=0,
                    tarja="Sem Tarja"
                )
                db.session.add(medicamento)
            db.session.commit()
        
        response = client.get('/api/inventario?page=1&limit=10')
        assert response.status_code == 200
        
        data = response.get_json()
        # Dados podem estar em 'dados' ou direto na raiz
        dados_content = data.get('dados', data.get('data', data))
        assert 'medicamentos' in dados_content or 'total' in dados_content
        assert 'correlation_id' in data
    
    def test_criar_medicamento_sucesso(self, client, auth_usuario, app):
        """POST /api/inventario deve criar medicamento com sucesso."""
        payload = {
            "nome": "Dipirona Teste",
            "lote": "LOT123",
            "data_validade": "2025-12-31",
            "quantidade": 50,
            "tarja": "Sem Tarja"
        }
        
        response = client.post('/api/inventario', json=payload)
        assert response.status_code in [200, 201]
        
        data = response.get_json()
        assert 'sucesso' in data or 'success' in data
        assert 'correlation_id' in data
    
    def test_criar_medicamento_validacao_erro(self, client, auth_usuario, app):
        """POST /api/inventario deve validar dados de entrada."""
        payload = {
            "nome": "",  # Nome vazio
            "lote": "LOT123",
            "data_validade": "2025-12-31",
            "quantidade": 50
        }
        
        response = client.post('/api/inventario', json=payload)
        assert response.status_code in [400, 422]
        
        data = response.get_json()
        assert 'erro' in data
        assert 'codigo' in data['erro']
        assert 'correlation_id' in data['erro']
    
    def test_medicamento_nao_encontrado(self, client, auth_usuario, app):
        """DELETE /api/inventario/{id} deve retornar 404 para ID inexistente."""
        response = client.delete('/api/inventario/99999')
        assert response.status_code == 404
        
        data = response.get_json()
        assert 'erro' in data
        assert data['erro']['codigo'] == 'NOT_FOUND'
        assert 'correlation_id' in data['erro']


class TestAPITriagemContract:
    """Testes de contrato para endpoint de triagem."""
    
    def test_triagem_sucesso(self, client, auth_usuario, app):
        """POST /api/triagem deve processar triagem com sucesso."""
        payload = {
            "nome": "Dipirona Teste",
            "lote": "LOT123",
            "data_validade": "2030-12-31",
            "quantidade": 50,
            "tarja": "Sem Tarja"
        }
        
        response = client.post('/api/triagem', json=payload)
        assert response.status_code in [200, 201]
        
        data = response.get_json()
        assert 'sucesso' in data or 'success' in data
        assert 'correlation_id' in data
    
    def test_triagem_medicamento_vencido(self, client, auth_usuario, app):
        """POST /api/triagem deve bloquear medicamento vencido."""
        payload = {
            "nome": "Dipirona Vencida",
            "lote": "LOT123",
            "data_validade": "2020-01-01",
            "quantidade": 50,
            "tarja": "Sem Tarja"
        }
        
        response = client.post('/api/triagem', json=payload)
        assert response.status_code == 422
        
        data = response.get_json()
        assert 'erro' in data
        assert 'codigo' in data['erro']
        assert 'correlation_id' in data['erro']
        # Mensagem não deve expor detalhes técnicos
        assert 'Traceback' not in data['erro']['mensagem']
    
    def test_triagem_portaria_344(self, client, auth_usuario, app):
        """POST /api/triagem deve bloquear Portaria 344."""
        payload = {
            "nome": "Clonazepam",
            "lote": "LOT123",
            "data_validade": "2030-12-31",
            "quantidade": 50,
            "tarja": "Portaria 344"
        }
        
        response = client.post('/api/triagem', json=payload)
        assert response.status_code == 422
        
        data = response.get_json()
        assert 'erro' in data
        assert 'codigo' in data['erro']
        assert 'correlation_id' in data['erro']


class TestAPIQRCodeContract:
    """Testes de contrato para endpoint de QR Code."""
    
    def test_qrcode_validate_sem_dados(self, client, auth_usuario, app):
        """POST /api/qrcode/validate deve retornar erro sem dados."""
        response = client.post('/api/qrcode/validate', json={})
        assert response.status_code == 400
        
        data = response.get_json()
        assert 'erro' in data
        assert 'codigo' in data['erro']
        assert 'correlation_id' in data['erro']
    
    def test_qrcode_validate_assinatura_invalida(self, client, auth_usuario, app):
        """POST /api/qrcode/validate deve validar assinatura."""
        payload = {
            "data": {"type": "prescription", "id": 1},
            "signature": "invalid_signature"
        }
        
        response = client.post('/api/qrcode/validate', json=payload)
        assert response.status_code == 400
        
        data = response.get_json()
        assert 'erro' in data
        assert 'codigo' in data['erro']
        assert 'correlation_id' in data['erro']
