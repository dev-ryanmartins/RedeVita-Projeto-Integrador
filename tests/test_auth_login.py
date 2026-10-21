"""
Test Auth Login - Suíte de Testes de Autenticação de Login
Testa o fluxo de login web para garantir que não há fallback para usuários incorretos
e que contas inativas não podem autenticar.
"""

import unittest
import sys
import os
import re

# Adiciona o diretório backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from main import create_app
from app.database import db
from app.models.usuario import Usuario
from app.core.security import criptografar_senha


class TestAuthLogin(unittest.TestCase):
    """Testa o fluxo de autenticação de login"""

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
            
            # Criar usuários de teste
            self.usuario_ativo = Usuario(
                nome='Usuário Ativo',
                cpf='12345678901',
                email='ativo@teste.local',
                senha=criptografar_senha('senha_correta'),
                cargo='Voluntário',
                ativo=True,
                senha_trocada=True
            )
            
            self.usuario_inativo = Usuario(
                nome='Usuário Inativo',
                cpf='98765432109',
                email='inativo@teste.local',
                senha=criptografar_senha('senha_correta'),
                cargo='Voluntário',
                ativo=False,
                senha_trocada=True
            )
            
            db.session.add(self.usuario_ativo)
            db.session.add(self.usuario_inativo)
            db.session.commit()
            
            # Store IDs for later use
            self.usuario_ativo_id = self.usuario_ativo.id
            self.usuario_inativo_id = self.usuario_inativo.id

    def _get_csrf_token(self, response):
        """Extract CSRF token from response"""
        # Try to get from cookies
        csrf_cookie = response.headers.get('Set-Cookie', '')
        if 'csrf_token' in csrf_cookie:
            # Extract token from cookie
            match = re.search(r'csrf_token=([^;]+)', csrf_cookie)
            if match:
                return match.group(1)
        
        # Try to get from form data (from GET response)
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

    def test_login_senha_incorreta_nao_autentica(self):
        """Testa que senha incorreta não autentica o usuário"""
        with self.app.app_context():
            response = self.client.get('/login')
            csrf_token = self._get_csrf_token(response)
            
            response = self.client.post('/login', data={
                'identificador': '12345678901',
                'senha': 'senha_errada',
                'csrf_token': csrf_token
            }, follow_redirects=False)
            
            self.assertNotEqual(response.status_code, 302)
            self.assertIn(b'CPF, e-mail ou senha incorretos', response.data)
            
            cookies = response.headers.get('Set-Cookie', '')
            self.assertNotIn('redevita_token', cookies)
            
            with self.client.session_transaction() as sess:
                self.assertIsNone(sess.get('usuario_id'))

    def test_login_cpf_inexistente_nao_autentica(self):
        """Testa que CPF inexistente não autentica nenhum usuário"""
        with self.app.app_context():
            response = self.client.get('/login')
            csrf_token = self._get_csrf_token(response)
            
            response = self.client.post('/login', data={
                'identificador': '11122233344',
                'senha': 'qualquer_senha',
                'csrf_token': csrf_token
            }, follow_redirects=False)
            
            self.assertNotEqual(response.status_code, 302)
            self.assertIn(b'CPF, e-mail ou senha incorretos', response.data)
            
            cookies = response.headers.get('Set-Cookie', '')
            self.assertNotIn('redevita_token', cookies)
            
            with self.client.session_transaction() as sess:
                self.assertIsNone(sess.get('usuario_id'))

    def test_login_email_inexistente_nao_autentica(self):
        """Testa que e-mail inexistente não autentica nenhum usuário"""
        with self.app.app_context():
            response = self.client.get('/login')
            csrf_token = self._get_csrf_token(response)
            
            response = self.client.post('/login', data={
                'identificador': 'naoexiste@teste.local',
                'senha': 'qualquer_senha',
                'csrf_token': csrf_token
            }, follow_redirects=False)
            
            self.assertNotEqual(response.status_code, 302)
            self.assertIn(b'CPF, e-mail ou senha incorretos', response.data)
            
            cookies = response.headers.get('Set-Cookie', '')
            self.assertNotIn('redevita_token', cookies)
            
            with self.client.session_transaction() as sess:
                self.assertIsNone(sess.get('usuario_id'))

    def test_login_conta_inativa_nao_autentica(self):
        """Testa que conta inativa não autentica, mesmo com senha correta"""
        with self.app.app_context():
            response = self.client.get('/login')
            csrf_token = self._get_csrf_token(response)
            
            response = self.client.post('/login', data={
                'identificador': '98765432109',
                'senha': 'senha_correta',
                'csrf_token': csrf_token
            }, follow_redirects=False)
            
            self.assertNotEqual(response.status_code, 302)
            self.assertIn(b'CPF, e-mail ou senha incorretos', response.data)
            
            cookies = response.headers.get('Set-Cookie', '')
            self.assertNotIn('redevita_token', cookies)
            
            with self.client.session_transaction() as sess:
                self.assertIsNone(sess.get('usuario_id'))

    def test_login_conta_ativa_credenciais_corretas_autentica(self):
        """Testa que credenciais corretas de conta ativa continuam funcionando"""
        with self.app.app_context():
            response = self.client.get('/login')
            csrf_token = self._get_csrf_token(response)
            
            response = self.client.post('/login', data={
                'identificador': '12345678901',
                'senha': 'senha_correta',
                'csrf_token': csrf_token
            }, follow_redirects=False)
            
            self.assertEqual(response.status_code, 302)
            self.assertIn('/dashboard', response.location)
            
            cookies = response.headers.get('Set-Cookie', '')
            self.assertIn('redevita_token', cookies)
            
            with self.client.session_transaction() as sess:
                self.assertEqual(sess.get('usuario_id'), self.usuario_ativo_id)
                self.assertEqual(sess.get('usuario_nome'), 'Usuário Ativo')
                self.assertEqual(sess.get('usuario_cargo'), 'Voluntário')

    def test_login_email_correto_conta_ativa_autentica(self):
        """Testa que login com e-mail correto de conta ativa funciona"""
        with self.app.app_context():
            response = self.client.get('/login')
            csrf_token = self._get_csrf_token(response)
            
            response = self.client.post('/login', data={
                'identificador': 'ativo@teste.local',
                'senha': 'senha_correta',
                'csrf_token': csrf_token
            }, follow_redirects=False)
            
            self.assertEqual(response.status_code, 302)
            self.assertIn('/dashboard', response.location)
            
            cookies = response.headers.get('Set-Cookie', '')
            self.assertIn('redevita_token', cookies)

    def test_nao_ha_fallback_para_usuario_id_1(self):
        """Testa que não há fallback para usuário id=1 quando credenciais são inválidas"""
        with self.app.app_context():
            usuario_id_1 = Usuario.query.filter_by(id=1).first()
            if usuario_id_1:
                usuario_id_1.nome = 'Usuario ID 1'
                db.session.commit()
            
            response = self.client.get('/login')
            csrf_token = self._get_csrf_token(response)
            
            response = self.client.post('/login', data={
                'identificador': '00000000000',
                'senha': 'senha_errada',
                'csrf_token': csrf_token
            }, follow_redirects=False)
            
            self.assertNotEqual(response.status_code, 302)
            self.assertIn(b'CPF, e-mail ou senha incorretos', response.data)
            
            cookies = response.headers.get('Set-Cookie', '')
            self.assertNotIn('redevita_token', cookies)

    def test_resposta_erro_generica_nao_revela_existencia(self):
        """Testa que a resposta de erro é genérica e não revela se o identificador existe"""
        with self.app.app_context():
            response1 = self.client.get('/login')
            csrf_token1 = self._get_csrf_token(response1)
            response1 = self.client.post('/login', data={
                'identificador': '12345678901',
                'senha': 'senha_errada',
                'csrf_token': csrf_token1
            }, follow_redirects=False)
            
            response2 = self.client.get('/login')
            csrf_token2 = self._get_csrf_token(response2)
            response2 = self.client.post('/login', data={
                'identificador': '99999999999',
                'senha': 'qualquer_senha',
                'csrf_token': csrf_token2
            }, follow_redirects=False)
            
            self.assertIn(b'CPF, e-mail ou senha incorretos', response1.data)
            self.assertIn(b'CPF, e-mail ou senha incorretos', response2.data)


if __name__ == '__main__':
    unittest.main(verbosity=2)
