"""
Test Provision Admin - Suíte de Testes de Provisionamento de Administrador
Testa o procedimento de provisionamento do primeiro administrador
"""

import unittest
import sys
import os
import tempfile
import subprocess

# Adiciona o diretório backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from main import create_app
from app.database import db
from app.models.usuario import Usuario
from app.core.security import criptografar_senha, verificar_senha


class TestProvisionAdmin(unittest.TestCase):
    """Testa o provisionamento de administrador"""

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

    def test_banco_vazio_sem_administrador(self):
        """Testa que banco vazio não tem administrador"""
        with self.app.app_context():
            admin = Usuario.query.filter_by(cargo='Admin').first()
            self.assertIsNone(admin)
            
            usuario = Usuario.query.first()
            self.assertIsNone(usuario)

    def test_inicializacao_normal_nao_cria_admin(self):
        """Testa que inicialização normal não cria administrador automaticamente"""
        with self.app.app_context():
            # Cria app novamente (simula inicialização normal)
            app2 = create_app({
                'TESTING': True,
                'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
                'WTF_CSRF_ENABLED': True,
            })
            
            with app2.app_context():
                db.create_all()
                
                # Verifica que não há administrador
                admin = Usuario.query.filter_by(cargo='Admin').first()
                self.assertIsNone(admin)

    def test_usuario_senha_trocada_flag(self):
        """Testa que campo senha_trocada existe e funciona"""
        with self.app.app_context():
            usuario = Usuario(
                nome='Teste',
                cpf='12345678901',
                email='teste@teste.local',
                senha=criptografar_senha('senha123'),
                cargo='Voluntário',
                ativo=True,
                senha_trocada=False
            )
            
            db.session.add(usuario)
            db.session.commit()
            
            # Recupera e verifica
            recuperado = Usuario.query.filter_by(cpf='12345678901').first()
            self.assertIsNotNone(recuperado)
            self.assertFalse(recuperado.senha_trocada)
            
            # Atualiza
            recuperado.senha_trocada = True
            db.session.commit()
            
            recuperado = Usuario.query.filter_by(cpf='12345678901').first()
            self.assertTrue(recuperado.senha_trocada)

    def test_login_redireciona_troca_senha_obrigatoria(self):
        """Testa que login com senha_trocada=False redireciona para troca obrigatória"""
        with self.app.app_context():
            # Cria usuário com senha_trocada=False
            usuario = Usuario(
                nome='Admin Teste',
                cpf='52998224725',
                email='admin@teste.local',
                senha=criptografar_senha('senha123'),
                cargo='Admin',
                ativo=True,
                senha_trocada=False
            )
            
            db.session.add(usuario)
            db.session.commit()
            
            # Faz login
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
            
            response = self.client.post('/login', data={
                'identificador': '52998224725',
                'senha': 'senha123',
                'csrf_token': csrf_token
            }, follow_redirects=False)
            
            # Deve redirecionar para trocar-senha-obrigatoria
            self.assertEqual(response.status_code, 302)
            self.assertIn('/trocar-senha-obrigatoria', response.location)

    def test_login_senha_trocada_true_vai_dashboard(self):
        """Testa que login com senha_trocada=True vai para dashboard"""
        with self.app.app_context():
            # Cria usuário com senha_trocada=True
            usuario = Usuario(
                nome='Admin Teste',
                cpf='39053344705',
                email='admin@teste.local',
                senha=criptografar_senha('senha123'),
                cargo='Admin',
                ativo=True,
                senha_trocada=True
            )
            
            db.session.add(usuario)
            db.session.commit()
            
            # Faz login
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
            
            response = self.client.post('/login', data={
                'identificador': '39053344705',
                'senha': 'senha123',
                'csrf_token': csrf_token
            }, follow_redirects=False)
            
            # Deve redirecionar para dashboard
            self.assertEqual(response.status_code, 302)
            self.assertIn('/dashboard', response.location)

    def test_troca_senha_obrigatoria_atualiza_flag(self):
        """Testa que rota de troca obrigatória atualiza senha_trocada"""
        with self.app.app_context():
            # Cria usuário com senha_trocada=False
            usuario = Usuario(
                nome='Admin Teste',
                cpf='71284738520',
                email='admin@teste.local',
                senha=criptografar_senha('senha123'),
                cargo='Admin',
                ativo=True,
                senha_trocada=False
            )
            
            db.session.add(usuario)
            db.session.commit()
            
            # Login para obter sessão
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
                'identificador': '71284738520',
                'senha': 'senha123',
                'csrf_token': csrf_token
            }, follow_redirects=False)
            
            # Troca senha
            response = self.client.get('/trocar-senha-obrigatoria')
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
            
            response = self.client.post('/trocar-senha-obrigatoria', data={
                'nova_senha': 'nova_senha_123',
                'confirmar_senha': 'nova_senha_123',
                'csrf_token': csrf_token
            }, follow_redirects=False)
            
            # Verifica redirecionamento para dashboard
            self.assertEqual(response.status_code, 302)
            self.assertIn('/dashboard', response.location)
            
            # Verifica flag atualizada
            usuario = Usuario.query.filter_by(cpf='71284738520').first()
            self.assertTrue(usuario.senha_trocada)
            self.assertTrue(verificar_senha(usuario.senha, 'nova_senha_123'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
