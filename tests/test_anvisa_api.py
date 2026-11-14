"""
Testes para P1.7: serviço ANVISA sem heurísticas permissivas
Verifica que falhas não resultam em aprovação automática
"""

import pytest
from main import create_app
from app.database import db
from app.utils.anvisa_api import ANVISAAPI, VerificationStatus


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
def anvisa_api():
    """Fixture para criar cliente ANVISA."""
    return ANVISAAPI()


class TestAnvisaAPIP17:
    """Testes para P1.7 - serviço ANVISA sem heurísticas permissivas."""
    
    def test_token_ausente_nao_resulta_em_aprovacao_automatica(self, anvisa_api):
        """Token ausente nunca resulta em aprovação automática nem em exige_receita=false."""
        # Cliente sem token configurado (força vazio)
        api = ANVISAAPI()
        api.token = ''
        
        # Verificar receita obrigatória
        resultado = api.verificar_receita_obrigatoria('Paracetamol', 'Sem Tarja')
        
        # Deve retornar None (não verificado), não False
        assert resultado['exige_receita'] is None
        assert resultado['status'] == VerificationStatus.NOT_VERIFIED.value
        assert resultado['pode_aprovar'] is False
        
        # Mensagem deve indicar desabilitado
        assert 'desabilitada' in resultado['mensagem']
    
    def test_verificar_regularidade_retorna_nao_verificado(self, anvisa_api):
        """Verificar regularidade retorna estado não verificado."""
        resultado = anvisa_api.verificar_regularidade('1234567890123')
        
        assert resultado['status'] == VerificationStatus.NOT_VERIFIED.value
        assert resultado['pode_aprovar'] is False
        assert 'não verificado' in resultado['situacao'].lower()
        assert 'desabilitado' in resultado['detalhes'].lower()
    
    def test_validar_portaria_344_retorna_falha(self, anvisa_api):
        """Validar Portaria 344 retorna falha (não aprova)."""
        valido, mensagem = anvisa_api.validar_portaria_344('1234567890123', 'Portaria 344')
        
        assert valido is False
        assert 'desabilitada' in mensagem
    
    def test_buscar_medicamentos_retorna_falha(self, anvisa_api):
        """Buscar medicamentos retorna falha."""
        sucesso, resultados, erro = anvisa_api.buscar_medicamentos_por_nome('Paracetamol')
        
        assert sucesso is False
        assert resultados is None
        assert 'desabilitado' in erro.lower()
    
    def test_heuristicas_de_nome_nao_substituem_confirmacao(self, anvisa_api):
        """Heurísticas de nome não substituem confirmação da fonte."""
        # Mesmo com nome de medicamento controlado, não aprova automaticamente
        resultado = anvisa_api.verificar_receita_obrigatoria('Diazepam', 'Sem Tarja')
        
        # Deve ser None (não verificado), não True baseado em heurística
        assert resultado['exige_receita'] is None
        assert resultado['status'] == VerificationStatus.NOT_VERIFIED.value
        assert resultado['pode_aprovar'] is False
    
    def test_tarja_controlada_classificada_corretamente(self, anvisa_api):
        """Tarja controlada é classificada corretamente, mas ainda não verificado."""
        resultado = anvisa_api.verificar_receita_obrigatoria('Diazepam', 'Portaria 344')
        
        # Classifica como exige receita baseado na tarja
        assert resultado['exige_receita'] is True
        assert resultado['tipo_receita'] == 'Receita de Controle Especial'
        
        # Mas status ainda é NOT_VERIFIED (API desabilitada)
        assert resultado['status'] == VerificationStatus.NOT_VERIFIED.value
        assert resultado['pode_aprovar'] is False
        assert 'desabilitada' in resultado['mensagem']
    
    def test_tarja_amarela_classificada_corretamente(self, anvisa_api):
        """Tarja amarela é classificada corretamente, mas ainda não verificado."""
        resultado = anvisa_api.verificar_receita_obrigatoria('Amoxicilina', 'Tarja Amarela')
        
        # Classifica como exige receita baseado na tarja
        assert resultado['exige_receita'] is True
        assert resultado['tipo_receita'] == 'Receita Simples'
        
        # Mas status ainda é NOT_VERIFIED (API desabilitada)
        assert resultado['status'] == VerificationStatus.NOT_VERIFIED.value
        assert resultado['pode_aprovar'] is False
    
    def test_sem_tarja_nao_assume_isento(self, anvisa_api):
        """Sem tarja não assume isento automaticamente."""
        resultado = anvisa_api.verificar_receita_obrigatoria('Paracetamol', 'Sem Tarja')
        
        # Deve ser None (não verificado), não False (isento)
        assert resultado['exige_receita'] is None
        assert resultado['status'] == VerificationStatus.NOT_VERIFIED.value
        assert resultado['pode_aprovar'] is False
        assert 'não foi possível verificar' in resultado['mensagem'].lower()
    
    def test_estado_nao_verificado_bloqueia_aprovacao(self, anvisa_api):
        """Estado não verificado bloqueia aprovação/reserva/dispensação automática."""
        resultado = anvisa_api.verificar_receita_obrigatoria('Paracetamol', 'Sem Tarja')
        
        # pode_aprovar deve ser sempre False
        assert resultado['pode_aprovar'] is False
        
        # status deve ser NOT_VERIFIED
        assert resultado['status'] == VerificationStatus.NOT_VERIFIED.value
        
        # alerta deve ser True (avisa que não foi verificado)
        assert resultado['alerta'] is True
    
    def test_fonte_e_data_consulta_registradas(self, anvisa_api):
        """Fonte e data/hora da consulta são registradas."""
        resultado = anvisa_api.verificar_receita_obrigatoria('Paracetamol', 'Sem Tarja')
        
        # Fonte deve indicar desabilitado
        assert 'desabilitada' in resultado['fonte'].lower()
        
        # Data de consulta deve estar presente
        assert 'data_consulta' in resultado
        assert resultado['data_consulta'] is not None
    
    def test_nenhum_token_em_logs(self, anvisa_api, caplog):
        """Nenhum token ou segredo aparece em logs."""
        # Configurar token falso
        api = ANVISAAPI()
        api.token = 'TOKEN_SECRETO_FAKE_12345'
        
        with caplog.at_level('WARNING'):
            resultado = api.verificar_receita_obrigatoria('Paracetamol', 'Sem Tarja')
        
        # Verificar que token não aparece nos logs
        for record in caplog.records:
            assert 'TOKEN_SECRETO_FAKE_12345' not in record.message
            assert 'token' not in record.message.lower() or len(record.message) < 50  # Não revela valor
    
    def test_consultar_medicamento_retorna_falha(self, anvisa_api):
        """Consultar medicamento retorna falha quando contrato não confirmado."""
        sucesso, dados, erro = anvisa_api.consultar_medicamento('1234567890123')
        
        assert sucesso is False
        assert dados is None
        assert 'endpoint desabilitado' in erro
