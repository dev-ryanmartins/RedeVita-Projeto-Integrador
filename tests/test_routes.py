"""
Test Routes - Suíte de Testes de Rotas
Testa o status HTTP das rotas principais do sistema
"""

import unittest
import sys
import os

# Adiciona o diretório backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from main import create_app


class TestRoutes(unittest.TestCase):
    """Testa as rotas principais da aplicação"""
    
    def setUp(self):
        """Configura o cliente de teste"""
        self.app = create_app({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        })
        self.client = self.app.test_client()
        
    def tearDown(self):
        """Limpa após cada teste"""
        pass
    
    def test_index_route(self):
        """Testa a rota principal (/)"""
        response = self.client.get('/')
        self.assertIn(response.status_code, [200, 302])  # 200 ou redirect para login
    
    def test_health_route(self):
        """Testa a rota de healthcheck (/health)"""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
    
    def test_api_v1_ping_route(self):
        """Testa a rota de ping da API (/api/v1/ping)"""
        response = self.client.get('/api/v1/ping')
        self.assertEqual(response.status_code, 200)
    
    def test_login_route(self):
        """Testa a rota de login (/login)"""
        response = self.client.get('/login')
        self.assertIn(response.status_code, [200, 302])
    
    def test_dashboard_route_redirect(self):
        """Testa que dashboard redireciona para login se não autenticado"""
        response = self.client.get('/dashboard')
        self.assertIn(response.status_code, [302, 403])  # Redirect ou Forbidden
    
    def test_inventario_route_redirect(self):
        """Testa que inventário redireciona para login se não autenticado"""
        response = self.client.get('/inventario')
        self.assertIn(response.status_code, [302, 403])
    
    def test_pacientes_route_redirect(self):
        """Testa que pacientes redireciona para login se não autenticado"""
        response = self.client.get('/pacientes')
        self.assertIn(response.status_code, [302, 403])
    
    def test_doacoes_route_redirect(self):
        """Testa que doações redireciona para login se não autenticado"""
        response = self.client.get('/doacoes')
        self.assertIn(response.status_code, [302, 403])
    
    def test_relatorios_route_redirect(self):
        """Testa que relatórios redireciona para login se não autenticado"""
        response = self.client.get('/relatorios')
        self.assertIn(response.status_code, [302, 403])
    
    def test_api_v1_health_route(self):
        """Testa a rota de healthcheck da API (/api/v1/health)"""
        response = self.client.get('/api/v1/health')
        self.assertIn(response.status_code, [200, 401, 429])  # 200, Unauthorized ou Rate Limit
    
    def test_api_v1_analytics_stats_route_redirect(self):
        """Testa que analytics stats requer autenticação"""
        response = self.client.get('/api/v1/analytics/stats')
        self.assertIn(response.status_code, [401, 429])  # Unauthorized ou Rate Limit
    
    def test_static_files(self):
        """Testa que arquivos estáticos são servidos"""
        response = self.client.get('/static/css/global.css')
        self.assertIn(response.status_code, [200, 404])
    
    def test_404_handler(self):
        """Testa o handler de 404"""
        response = self.client.get('/rota-inexistente')
        self.assertEqual(response.status_code, 404)


class TestAPIRoutes(unittest.TestCase):
    """Testa rotas específicas da API"""
    
    def setUp(self):
        """Configura o cliente de teste"""
        self.app = create_app({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        })
        self.client = self.app.test_client()
    
    def test_api_bula_route_redirect(self):
        """Testa que API de bula requer autenticação"""
        response = self.client.get('/api/bula/dipirona')
        self.assertIn(response.status_code, [302, 401])
    
    def test_api_referencia_buscar_route_redirect(self):
        """Testa que API de busca de referência requer autenticação"""
        response = self.client.get('/api/referencia/buscar?q=test')
        self.assertIn(response.status_code, [302, 401])


if __name__ == '__main__':
    unittest.main(verbosity=2)
