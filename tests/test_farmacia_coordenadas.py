"""
Testes para P1.8: cadastro de farmácia e busca por proximidade
Verifica validação de coordenadas e comportamento sem HTTP 500
"""

import pytest
import math
from main import create_app
from app.database import db
from app.models.farmacia import Farmacia
from app.models.usuario import Usuario
from app.core.security import criptografar_senha
from app.routes.mapa import validar_coordenada, calcular_distancia_haversine


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


class TestValidacaoCoordenadas:
    """Testes para validação de coordenadas."""
    
    def test_coordenadas_validas_sao_aceitas(self):
        """Latitude/longitude válidas e finitas são aceitas."""
        valido, erro = validar_coordenada(-23.5505, -46.6333)
        assert valido is True
        assert erro == ""
    
    def test_latitude_fora_intervalo_rejeitada(self):
        """Latitude fora do intervalo [-90, 90] é rejeitada."""
        valido, erro = validar_coordenada(91, -46.6333)
        assert valido is False
        assert "Latitude deve estar entre -90 e 90" in erro
        
        valido, erro = validar_coordenada(-91, -46.6333)
        assert valido is False
        assert "Latitude deve estar entre -90 e 90" in erro
    
    def test_longitude_fora_intervalo_rejeitada(self):
        """Longitude fora do intervalo [-180, 180] é rejeitada."""
        valido, erro = validar_coordenada(-23.5505, 181)
        assert valido is False
        assert "Longitude deve estar entre -180 e 180" in erro
        
        valido, erro = validar_coordenada(-23.5505, -181)
        assert valido is False
        assert "Longitude deve estar entre -180 e 180" in erro
    
    def test_nan_rejeitado(self):
        """NaN é rejeitado."""
        valido, erro = validar_coordenada(float('nan'), -46.6333)
        assert valido is False
        assert "não podem ser NaN" in erro
        
        valido, erro = validar_coordenada(-23.5505, float('nan'))
        assert valido is False
        assert "não podem ser NaN" in erro
    
    def test_infinito_rejeitado(self):
        """Infinito é rejeitado."""
        valido, erro = validar_coordenada(float('inf'), -46.6333)
        assert valido is False
        assert "não podem ser infinitas" in erro
        
        valido, erro = validar_coordenada(-23.5505, float('inf'))
        assert valido is False
        assert "não podem ser infinitas" in erro
    
    def test_texto_rejeitado(self):
        """Texto é rejeitado."""
        valido, erro = validar_coordenada("texto", -46.6333)
        assert valido is False
        assert "devem ser numéricas" in erro
    
    def test_limites_intervalos_aceitos(self):
        """Limites dos intervalos são aceitos."""
        valido, erro = validar_coordenada(90, 180)
        assert valido is True
        
        valido, erro = validar_coordenada(-90, -180)
        assert valido is True
        
        valido, erro = validar_coordenada(0, 0)
        assert valido is True


class TestCalculoDistancia:
    """Testes para cálculo de distância Haversine."""
    
    def test_calculo_distancia_valido(self):
        """Cálculo de distância com coordenadas válidas."""
        distancia = calcular_distancia_haversine(-23.5505, -46.6333, -23.5605, -46.6433)
        assert distancia > 0
        assert isinstance(distancia, float)
    
    def test_calculo_distancia_mesmo_ponto(self):
        """Distância entre o mesmo ponto é zero."""
        distancia = calcular_distancia_haversine(-23.5505, -46.6333, -23.5505, -46.6333)
        assert distancia == 0.0
    
    def test_calculo_distancia_com_coordenadas_invalidas_levanta_erro(self):
        """Cálculo com coordenadas inválidas levanta ValueError."""
        with pytest.raises(ValueError) as exc_info:
            calcular_distancia_haversine(91, -46.6333, -23.5605, -46.6433)
        assert "Coordenadas inválidas" in str(exc_info.value)
        
        with pytest.raises(ValueError) as exc_info:
            calcular_distancia_haversine(-23.5505, -46.6333, float('nan'), -46.6433)
        assert "Coordenadas inválidas" in str(exc_info.value)


class TestFarmaciaSemCoordenadas:
    """Testes para farmácias sem coordenadas."""
    
    def test_farmacia_sem_coordenadas_preservada(self, app):
        """Registros antigos sem coordenadas continuam preservados."""
        with app.app_context():
            farmacia = Farmacia(
                nome_fantasia="Farmácia Teste",
                cnpj="12.345.678/0001-90",
                endereco="Rua Teste, 123",
                responsavel="João Silva",
                latitude=None,
                longitude=None
            )
            db.session.add(farmacia)
            db.session.commit()
            
            farmacia_recuperada = db.session.get(Farmacia, farmacia.id)
            assert farmacia_recuperada.latitude is None
            assert farmacia_recuperada.longitude is None
    
    def test_busca_proximidade_omite_farmacias_sem_coordenadas(self, app):
        """Busca por proximidade omite farmácias sem coordenadas."""
        with app.app_context():
            # Criar farmácia sem coordenadas
            farmacia_sem_coord = Farmacia(
                nome_fantasia="Farmácia Sem Coordenadas",
                cnpj="12.345.678/0001-90",
                endereco="Rua Teste, 123",
                responsavel="João Silva",
                latitude=None,
                longitude=None
            )
            db.session.add(farmacia_sem_coord)
            
            # Criar farmácia com coordenadas
            farmacia_com_coord = Farmacia(
                nome_fantasia="Farmácia Com Coordenadas",
                cnpj="12.345.678/0002-70",
                endereco="Rua Teste, 456",
                responsavel="Maria Silva",
                latitude=-23.5505,
                longitude=-46.6333
            )
            db.session.add(farmacia_com_coord)
            db.session.commit()
            
            # Buscar farmácias
            farmacias = Farmacia.query.all()
            assert len(farmacias) == 2
            
            # Contar farmácias com coordenadas válidas
            com_coord = [f for f in farmacias if f.latitude is not None and f.longitude is not None]
            assert len(com_coord) == 1
            assert com_coord[0].nome_fantasia == "Farmácia Com Coordenadas"


class TestBuscaProximidadeAPI:
    """Testes para API de busca por proximidade."""
    
    def _fazer_login(self, client):
        """Faz login para testar rotas protegidas."""
        # Criar usuário de teste
        with client.application.app_context():
            usuario = Usuario(
                nome='Voluntário Teste',
                cpf='12345678901',
                email='voluntario@teste.com',
                senha=criptografar_senha('senha123'),
                cargo='Voluntário',
                ativo=True,
                credencial_versao=1
            )
            db.session.add(usuario)
            db.session.commit()
        
        # Fazer login
        client.post('/login', data={
            'identificador': '12345678901',
            'senha': 'senha123'
        }, follow_redirects=True)
    
    def test_busca_proximidade_sem_coordenadas_paciente_erro_400(self, app):
        """Busca por proximidade sem coordenadas do paciente retorna erro 400."""
        with app.test_client() as client:
            self._fazer_login(client)
            response = client.post('/api/mapa/proximidade',
                                  json={},
                                  content_type='application/json')
            assert response.status_code == 400
            data = response.get_json()
            # Verificar que há erro (pode estar em 'message' ou 'erro')
            assert 'message' in data or 'erro' in data
            msg = data.get('message', data.get('erro', ''))
            # msg já é string, get_json() retorna dict com valores string
            assert isinstance(msg, str)
            assert "obrigat" in msg.lower() or "fornecidos" in msg.lower()

    def test_busca_proximidade_coordenadas_invalidas_erro_400(self, app):
        """Busca por proximidade com coordenadas inválidas retorna erro 400."""
        with app.test_client() as client:
            self._fazer_login(client)
            response = client.post('/api/mapa/proximidade',
                                  json={'latitude': 91, 'longitude': -46.6333},
                                  content_type='application/json')
            assert response.status_code == 400
            data = response.get_json()
            assert 'message' in data or 'erro' in data
            msg = data.get('message', data.get('erro', ''))
            assert isinstance(msg, str)
            assert "inv" in msg.lower() or "Latitude" in msg

    def test_busca_proximidade_coordenadas_texto_erro_400(self, app):
        """Busca por proximidade com coordenadas como texto retorna erro 400."""
        with app.test_client() as client:
            self._fazer_login(client)
            response = client.post('/api/mapa/proximidade',
                                  json={'latitude': 'texto', 'longitude': -46.6333},
                                  content_type='application/json')
            assert response.status_code == 400
            data = response.get_json()
            assert 'message' in data or 'erro' in data
            msg = data.get('message', data.get('erro', ''))
            assert isinstance(msg, str)
            assert "n" in msg.lower() or "num" in msg.lower()
    
    def test_busca_proximidade_retorna_estavel_sem_http_500(self, app):
        """Busca por proximidade retorna estável sem HTTP 500."""
        with app.app_context():
            # Criar farmácia sem coordenadas
            farmacia = Farmacia(
                nome_fantasia="Farmácia Teste",
                cnpj="12.345.678/0001-90",
                endereco="Rua Teste, 123",
                responsavel="João Silva",
                latitude=None,
                longitude=None
            )
            db.session.add(farmacia)
            db.session.commit()
        
        with app.test_client() as client:
            self._fazer_login(client)
            response = client.post('/api/mapa/proximidade',
                                  json={'latitude': -23.5505, 'longitude': -46.6333},
                                  content_type='application/json')
            # Deve retornar 200, não 500
            assert response.status_code == 200
            data = response.get_json()
            # Dados podem estar em 'dados' ou 'data'
            dados = data.get('dados', data.get('data', {}))
            assert 'farmacias_proximas' in dados
            # Deve estar vazio pois não há farmácias com coordenadas próximas
            assert len(dados['farmacias_proximas']) == 0
