"""
Test Auth Cadastro - Suíte de Testes de Cadastro Público
Testa o fluxo de cadastro público para garantir que não é possível escolher papéis privilegiados
"""

import unittest
import sys
import os

# Adiciona o diretório backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from main import create_app
from app.database import db
from app.models.usuario import Usuario


class TestAuthCadastro(unittest.TestCase):
    """Testa o fluxo de cadastro público"""

    def setUp(self):
        """Configura o cliente de teste e banco de dados"""
        self.app = create_app({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'WTF_CSRF_ENABLED': True,  # Enable CSRF for security testing
        })
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()

    def _get_csrf_token(self, response):
        """Extract CSRF token from response"""
        import re
        # Try to get from cookies
        csrf_cookie = response.headers.get('Set-Cookie', '')
        if 'csrf_token' in csrf_cookie:
            match = re.search(r'csrf_token=([^;]+)', csrf_cookie)
            if match:
                return match.group(1)
        
        # Try to get from form data
        if hasattr(response, 'data'):
            match = re.search(r'name="csrf_token".*?value="([^"]+)"', response.data.decode('utf-8'))
            if match:
                return match.group(1)
        
        return None

    def tearDown(self):
        """Limpa após cada teste"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_cadastro_ignora_cargo_admin(self):
        """Testa que enviar cargo=Admin no cadastro público concede apenas Voluntário"""
        with self.app.app_context():
            response = self.client.get('/cadastro')
            csrf_token = self._get_csrf_token(response)
            
            response = self.client.post('/cadastro', data={
                'nome': 'Teste Admin',
                'cpf': '52998224725',
                'email': 'admin@teste.local',
                'senha': 'SenhaValida123@',
                'confirmar_senha': 'SenhaValida123@',
                'cargo': 'Admin',
                'csrf_token': csrf_token
            }, follow_redirects=False)
            
            self.assertEqual(response.status_code, 302)
            
            usuario = Usuario.query.filter_by(cpf='52998224725').first()
            self.assertIsNotNone(usuario)
            self.assertEqual(usuario.cargo, 'Voluntário')

    def test_cadastro_ignora_cargo_medico(self):
        """Testa que enviar cargo=Médico no cadastro público concede apenas Voluntário"""
        with self.app.app_context():
            response = self.client.get('/cadastro')
            csrf_token = self._get_csrf_token(response)
            
            response = self.client.post('/cadastro', data={
                'nome': 'Teste Médico',
                'cpf': '39053344705',
                'email': 'medico@teste.local',
                'senha': 'SenhaValida123@',
                'confirmar_senha': 'SenhaValida123@',
                'cargo': 'Médico',
                'csrf_token': csrf_token
            }, follow_redirects=False)
            
            self.assertEqual(response.status_code, 302)
            
            usuario = Usuario.query.filter_by(cpf='39053344705').first()
            self.assertIsNotNone(usuario)
            self.assertEqual(usuario.cargo, 'Voluntário')


if __name__ == '__main__':
    unittest.main(verbosity=2)
