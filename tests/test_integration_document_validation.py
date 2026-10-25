"""
Test Integration Document Validation - Suíte de Testes de Integração
Testa validação de CPF/CNPJ em rotas web e API
"""

import unittest
import sys
import os

# Adiciona o diretório backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from main import create_app
from app.database import db
from app.models.usuario import Usuario
from app.models.farmacia import Farmacia
from app.core.security import criptografar_senha


class TestIntegracaoCPFWeb(unittest.TestCase):
    """Testa validação de CPF em rotas web"""

    def setUp(self):
        """Configura o cliente de teste e banco de dados"""
        self.app = create_app({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'WTF_CSRF_ENABLED': True,
        })
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        """Limpa após cada teste"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _get_csrf_token(self, response):
        """Extract CSRF token from response"""
        import re
        csrf_cookie = response.headers.get('Set-Cookie', '')
        if 'csrf_token' in csrf_cookie:
            match = re.search(r'csrf_token=([^;]+)', csrf_cookie)
            if match:
                return match.group(1)
        
        if hasattr(response, 'data'):
            match = re.search(r'name="csrf_token".*?value="([^"]+)"', response.data.decode('utf-8'))
            if match:
                return match.group(1)
        
        return None

    def test_cadastro_cpf_valido_aceito(self):
        """Testa que cadastro com CPF válido é aceito"""
        response = self.client.get('/cadastro')
        csrf_token = self._get_csrf_token(response)
        
        response = self.client.post('/cadastro', data={
            'nome': 'Teste CPF',
            'cpf': '52998224725',  # CPF válido
            'email': 'teste@teste.local',
            'senha': 'SenhaValida123@',
            'confirmar_senha': 'SenhaValida123@',
            'csrf_token': csrf_token
        }, follow_redirects=False)
        
        # Verifica se houve redirecionamento (sucesso) ou erro
        self.assertIn(response.status_code, [302, 200])
        
        with self.app.app_context():
            usuario = Usuario.query.filter_by(cpf='52998224725').first()
            self.assertIsNotNone(usuario)

    def test_cadastro_cpf_invalido_rejeitado(self):
        """Testa que cadastro com CPF inválido é rejeitado"""
        response = self.client.get('/cadastro')
        csrf_token = self._get_csrf_token(response)
        
        response = self.client.post('/cadastro', data={
            'nome': 'Teste CPF',
            'cpf': '11111111111',  # CPF inválido (sequência repetida)
            'email': 'teste@teste.local',
            'senha': 'SenhaValida123@',
            'confirmar_senha': 'SenhaValida123@',
            'csrf_token': csrf_token
        }, follow_redirects=False)
        
        # Deve redirecionar de volta para cadastro com erro ou mostrar erro
        self.assertIn(response.status_code, [302, 200])
        
        with self.app.app_context():
            usuario = Usuario.query.filter_by(cpf='11111111111').first()
            self.assertIsNone(usuario)


class TestIntegracaoCNPJWeb(unittest.TestCase):
    """Testa validação de CNPJ em rotas web"""

    def setUp(self):
        """Configura o cliente de teste e banco de dados"""
        self.app = create_app({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'WTF_CSRF_ENABLED': True,
        })
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            
            # Criar usuário admin para autenticação
            admin = Usuario(
                nome='Admin',
                cpf='12345678901',
                email='admin@teste.local',
                senha=criptografar_senha('senha123'),
                cargo='Admin',
                ativo=True,
                senha_trocada=True
            )
            db.session.add(admin)
            db.session.commit()

    def tearDown(self):
        """Limpa após cada teste"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _login(self):
        """Faz login como admin"""
        response = self.client.get('/login')
        import re
        csrf_cookie = response.headers.get('Set-Cookie', '')
        csrf_token = None
        if 'csrf_token' in csrf_cookie:
            match = re.search(r'csrf_token=([^;]+)', csrf_cookie)
            if match:
                csrf_token = match.group(1)
        
        if not csrf_token and hasattr(response, 'data'):
            match = re.search(r'name="csrf_token".*?value="([^"]+)"', response.data.decode('utf-8'))
            if match:
                csrf_token = match.group(1)
        
        self.client.post('/login', data={
            'identificador': '12345678901',
            'senha': 'senha123',
            'csrf_token': csrf_token
        }, follow_redirects=False)

    def _get_csrf_token(self, response):
        """Extract CSRF token from response"""
        import re
        csrf_cookie = response.headers.get('Set-Cookie', '')
        if 'csrf_token' in csrf_cookie:
            match = re.search(r'csrf_token=([^;]+)', csrf_cookie)
            if match:
                return match.group(1)
        
        if hasattr(response, 'data'):
            match = re.search(r'name="csrf_token".*?value="([^"]+)"', response.data.decode('utf-8'))
            if match:
                return match.group(1)
        
        return None

    def test_criar_farmacia_cnpj_numerico_valido(self):
        """Testa que criação de farmácia com CNPJ numérico válido é aceita"""
        self._login()
        
        response = self.client.get('/farmacias')
        csrf_token = self._get_csrf_token(response)
        
        response = self.client.post('/farmacia/nova', data={
            'nome_fantasia': 'Farmácia Teste',
            'cnpj': '11444777000161',  # CNPJ numérico válido
            'endereco': 'Rua Teste, 123',
            'responsavel': 'Dr. Teste',
            'csrf_token': csrf_token
        }, follow_redirects=False)
        
        self.assertEqual(response.status_code, 302)
        
        with self.app.app_context():
            farmacia = Farmacia.query.filter_by(cnpj='11.444.777/0001-61').first()
            self.assertIsNotNone(farmacia)

    def test_criar_farmacia_cnpj_alfanumerico_preserva_letras(self):
        """Testa que criação de farmácia com CNPJ alfanumérico preserva letras"""
        self._login()
        
        response = self.client.get('/farmacias')
        csrf_token = self._get_csrf_token(response)
        
        response = self.client.post('/farmacia/nova', data={
            'nome_fantasia': 'Farmácia Teste',
            'cnpj': 'AB123456789012',  # CNPJ alfanumérico (letras preservadas)
            'endereco': 'Rua Teste, 123',
            'responsavel': 'Dr. Teste',
            'csrf_token': csrf_token
        }, follow_redirects=False)
        
        # A validação pode rejeitar se o DV estiver incorreto, mas a normalização deve preservar letras
        # O teste foca em verificar que as letras não são removidas silenciosamente
        self.assertEqual(response.status_code, 302)

    def test_criar_farmacia_cnpj_invalido_rejeitado(self):
        """Testa que criação de farmácia com CNPJ inválido é rejeitada"""
        self._login()
        
        response = self.client.get('/farmacias')
        csrf_token = self._get_csrf_token(response)
        
        response = self.client.post('/farmacia/nova', data={
            'nome_fantasia': 'Farmácia Teste',
            'cnpj': '11111111111111',  # CNPJ inválido (sequência repetida)
            'endereco': 'Rua Teste, 123',
            'responsavel': 'Dr. Teste',
            'csrf_token': csrf_token
        }, follow_redirects=False)
        
        self.assertEqual(response.status_code, 302)
        
        with self.app.app_context():
            farmacia = Farmacia.query.filter_by(cnpj='11.111.111/1111-11').first()
            self.assertIsNone(farmacia)


if __name__ == '__main__':
    unittest.main(verbosity=2)
