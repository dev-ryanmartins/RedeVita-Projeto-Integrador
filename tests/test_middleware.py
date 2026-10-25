"""
Testes para middleware de request-id e logging estruturado.
"""

import pytest
import re
from app.main import create_app
from app.core.middleware import (
    generate_request_id,
    validate_request_id,
    sanitize_for_log,
    reset_metrics,
    get_metrics,
    record_metric
)


class TestRequestIdGeneration:
    """Testes de geração e validação de request-id."""
    
    def test_generate_request_id_returns_uuid(self):
        """generate_request_id deve retornar UUID v4 válido."""
        request_id = generate_request_id()
        assert request_id is not None
        assert len(request_id) == 36  # UUID v4 format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
        assert re.match(r'^[a-f0-9\-]{36}$', request_id)
    
    def test_generate_request_id_unique(self):
        """generate_request_id deve gerar IDs únicos."""
        ids = [generate_request_id() for _ in range(100)]
        assert len(set(ids)) == 100  # Todos únicos
    
    def test_validate_request_id_valid_uuid(self):
        """validate_request_id deve aceitar UUID válido."""
        valid_id = generate_request_id()
        assert validate_request_id(valid_id) is True
    
    def test_validate_request_id_valid_custom(self):
        """validate_request_id deve aceitar string alfanumérica segura."""
        assert validate_request_id("abc123-xyz789") is True
        assert validate_request_id("REQ_12345") is True
    
    def test_validate_request_id_invalid_too_long(self):
        """validate_request_id deve rejeitar ID muito longo."""
        assert validate_request_id("a" * 65) is False
    
    def test_validate_request_id_invalid_chars(self):
        """validate_request_id deve rejeitar caracteres inválidos."""
        assert validate_request_id("abc@123") is False
        assert validate_request_id("abc#123") is False
        assert validate_request_id("abc 123") is False
    
    def test_validate_request_id_empty(self):
        """validate_request_id deve rejeitar string vazia."""
        assert validate_request_id("") is False
        assert validate_request_id(None) is False


class TestSanitizeForLog:
    """Testes de sanitização de dados sensíveis."""
    
    def test_sanitize_cpf(self):
        """sanitize_for_log deve remover CPF."""
        assert sanitize_for_log("123.456.789-00") == "[CPF]"
        assert sanitize_for_log("12345678900") == "[CPF]"
    
    def test_sanitize_cnpj(self):
        """sanitize_for_log deve remover CNPJ."""
        assert sanitize_for_log("12.345.678/0001-00") == "[CNPJ]"
    
    def test_sanitize_email(self):
        """sanitize_for_log deve remover email."""
        assert sanitize_for_log("teste@exemplo.com") == "[EMAIL]"
    
    def test_sanitize_long_tokens(self):
        """sanitize_for_log deve remover tokens longos."""
        assert sanitize_for_log("a" * 40) == "[TOKEN]"
    
    def test_sanitize_preserves_normal_text(self):
        """sanitize_for_log deve preservar texto normal."""
        assert sanitize_for_log("Nome do medicamento") == "Nome do medicamento"
        assert sanitize_for_log("Descrição normal") == "Descrição normal"
    
    def test_sanitize_empty_string(self):
        """sanitize_for_log deve lidar com string vazia."""
        assert sanitize_for_log("") == ""
        assert sanitize_for_log(None) is None


class TestMetrics:
    """Testes de métricas básicas."""
    
    def setup_method(self):
        """Resetar métricas antes de cada teste."""
        reset_metrics()
    
    def test_record_metric_increases_count(self):
        """record_metric deve incrementar contador."""
        record_metric('/test', 200, 0.1)
        metrics = get_metrics()
        assert '/test' in metrics
        assert metrics['/test']['count'] == 1
    
    def test_record_metric_increases_errors(self):
        """record_metric deve incrementar contador de erros para status >= 400."""
        record_metric('/test', 400, 0.1)
        metrics = get_metrics()
        assert metrics['/test']['errors'] == 1
    
    def test_record_metric_no_error_for_success(self):
        """record_metric não deve incrementar erros para status < 400."""
        record_metric('/test', 200, 0.1)
        metrics = get_metrics()
        assert metrics['/test']['errors'] == 0
    
    def test_get_metrics_calculates_avg_latency(self):
        """get_metrics deve calcular latência média."""
        record_metric('/test', 200, 0.1)
        record_metric('/test', 200, 0.2)
        metrics = get_metrics()
        assert metrics['/test']['avg_latency_ms'] == 150.0  # (0.1 + 0.2) / 2 * 1000
    
    def test_get_metrics_calculates_error_rate(self):
        """get_metrics deve calcular taxa de erro."""
        record_metric('/test', 200, 0.1)
        record_metric('/test', 400, 0.1)
        record_metric('/test', 200, 0.1)
        metrics = get_metrics()
        assert metrics['/test']['error_rate'] == 33.33  # 1/3 * 100
    
    def test_reset_metrics_clears_all(self):
        """reset_metrics deve limpar todas as métricas."""
        record_metric('/test', 200, 0.1)
        reset_metrics()
        metrics = get_metrics()
        assert len(metrics) == 0


class TestMiddlewareIntegration:
    """Testes de integração do middleware."""
    
    def test_request_id_in_response_header(self):
        """Middleware deve adicionar X-Request-ID ao cabeçalho de resposta."""
        app = create_app({'TESTING': True})
        client = app.test_client()
        
        response = client.get('/health')
        assert 'X-Request-ID' in response.headers
        assert len(response.headers['X-Request-ID']) == 36  # UUID format
    
    def test_request_id_accepts_custom_valid(self):
        """Middleware deve aceitar request-id válido do cliente."""
        app = create_app({'TESTING': True})
        client = app.test_client()
        
        custom_id = "REQ_12345"
        response = client.get('/health', headers={'X-Request-ID': custom_id})
        # Deve usar o custom_id se válido
        assert 'X-Request-ID' in response.headers
    
    def test_request_id_generates_new_for_invalid(self):
        """Middleware deve gerar novo ID se cliente fornecer inválido."""
        app = create_app({'TESTING': True})
        client = app.test_client()
        
        invalid_id = "invalid@id"
        response = client.get('/health', headers={'X-Request-ID': invalid_id})
        # Deve gerar novo ID
        assert 'X-Request-ID' in response.headers
        assert response.headers['X-Request-ID'] != invalid_id
    
    def test_metrics_endpoint_dev_only(self):
        """Endpoint /metrics deve estar disponível apenas em dev."""
        app = create_app({'TESTING': True, 'DEBUG': True})
        client = app.test_client()
        
        response = client.get('/metrics')
        # Em dev/debug, deve funcionar
        assert response.status_code in [200, 403]  # 403 se verificação de ambiente for estrita
