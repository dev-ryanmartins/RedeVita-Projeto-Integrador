"""
Testes para o serviço de triagem de medicamentos (P2.2).
"""

import pytest
from datetime import datetime, date
from app.services.triagem_service import TriagemMedicamentoService, TriagemError, TARJAS_VALIDAS


class TestTriagemMedicamentoService:
    """Testes para o serviço de triagem de medicamentos."""
    
    def test_validar_entrada_campos_obrigatorios(self):
        """Validação deve falhar se campos obrigatórios estiverem vazios."""
        with pytest.raises(TriagemError) as exc_info:
            TriagemMedicamentoService.validar_entrada("", "123", "2025-12-31", "10")
        assert "Preencha todos os campos obrigatórios" in str(exc_info.value)
    
    def test_validar_entrada_quantidade_invalida(self):
        """Validação deve falhar se quantidade for inválida."""
        with pytest.raises(TriagemError) as exc_info:
            TriagemMedicamentoService.validar_entrada("Dipirona", "123", "2025-12-31", "abc")
        assert "Quantidade inválida" in str(exc_info.value)
    
    def test_validar_entrada_quantidade_zero(self):
        """Validação deve falhar se quantidade for zero ou negativa."""
        with pytest.raises(TriagemError) as exc_info:
            TriagemMedicamentoService.validar_entrada("Dipirona", "123", "2025-12-31", "0")
        assert "Quantidade inválida" in str(exc_info.value)
        
        with pytest.raises(TriagemError) as exc_info:
            TriagemMedicamentoService.validar_entrada("Dipirona", "123", "2025-12-31", "-5")
        assert "Quantidade inválida" in str(exc_info.value)
    
    def test_validar_entrada_data_invalida(self):
        """Validação deve falhar se data for inválida."""
        with pytest.raises(TriagemError) as exc_info:
            TriagemMedicamentoService.validar_entrada("Dipirona", "123", "32/13/2025", "10")
        assert "Data de validade inválida" in str(exc_info.value)
    
    def test_validar_entrada_sucesso(self):
        """Validação deve sucesso com dados corretos."""
        valido, erro, dados = TriagemMedicamentoService.validar_entrada(
            "Dipirona", "123", "2025-12-31", "10"
        )
        assert valido is True
        assert erro is None
        assert dados["nome"] == "Dipirona"
        assert dados["lote"] == "123"
        assert dados["quantidade"] == 10
        assert dados["tarja"] == "Sem Tarja"
    
    def test_validar_entrada_tarja_normalizada(self):
        """Tarja inválida deve ser normalizada para 'Sem Tarja'."""
        valido, erro, dados = TriagemMedicamentoService.validar_entrada(
            "Dipirona", "123", "2025-12-31", "10", tarja="TarjaInvalida"
        )
        assert dados["tarja"] == "Sem Tarja"
    
    def test_validar_regras_negocio_medicamento_vencido(self):
        """Validação deve bloquear medicamentos vencidos."""
        dados = {
            "nome": "Dipirona",
            "lote": "123",
            "data_validade": date(2020, 1, 1),  # Data passada
            "quantidade": 10,
            "tarja": "Sem Tarja",
            "principio_ativo": None,
        }
        with pytest.raises(TriagemError) as exc_info:
            TriagemMedicamentoService.validar_regras_negocio(dados)
        assert "vencidos" in str(exc_info.value).lower()
    
    def test_validar_regras_negocio_portaria_344(self):
        """Validação deve bloquear Portaria 344."""
        dados = {
            "nome": "Clonazepam",
            "lote": "123",
            "data_validade": date(2030, 12, 31),  # Data futura
            "quantidade": 10,
            "tarja": "Portaria 344",
            "principio_ativo": "Clonazepam",
        }
        with pytest.raises(TriagemError) as exc_info:
            TriagemMedicamentoService.validar_regras_negocio(dados)
        assert "Portaria 344" in str(exc_info.value)
    
    def test_validar_regras_negocio_principio_controlado(self):
        """Validação deve bloquear princípios ativos controlados."""
        dados = {
            "nome": "Antibiótico Teste",
            "lote": "123",
            "data_validade": date(2030, 12, 31),  # Data futura
            "quantidade": 10,
            "tarja": "Tarja Amarela",
            "principio_ativo": "antibiotico test",
        }
        with pytest.raises(TriagemError) as exc_info:
            TriagemMedicamentoService.validar_regras_negocio(dados)
        assert "controladas" in str(exc_info.value).lower()
    
    def test_validar_regras_negocio_sucesso(self):
        """Validação deve sucesso com dados válidos."""
        dados = {
            "nome": "Dipirona",
            "lote": "123",
            "data_validade": date(2030, 12, 31),  # Data futura
            "quantidade": 10,
            "tarja": "Sem Tarja",
            "principio_ativo": "Dipirona Sódica",
        }
        valido, erro = TriagemMedicamentoService.validar_regras_negocio(dados)
        assert valido is True
        assert erro is None
        assert "status_semaforo" in dados
    
    def test_obter_tarjas_validas(self):
        """Deve retornar lista de tarjas válidas."""
        tarjas = TriagemMedicamentoService.obter_tarjas_validas()
        assert isinstance(tarjas, list)
        assert "Sem Tarja" in tarjas
        assert "Tarja Amarela" in tarjas
        assert "Tarja Vermelha" in tarjas
        assert "Portaria 344" in tarjas
        assert len(tarjas) == 4
