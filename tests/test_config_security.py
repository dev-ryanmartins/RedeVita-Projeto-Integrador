"""
Test Config Security - Suíte de Testes de Configuração de Segurança
Testa que a configuração de segurança está corretamente definida
"""

import unittest
import sys
import os

# Adiciona o diretório backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


class TestConfigSecurity(unittest.TestCase):
    """Testa a configuração de segurança"""

    def test_csrf_habilitado_por_padrao(self):
        """Testa que CSRF está habilitado por padrão"""
        from app.config import Config
        config = Config()
        self.assertTrue(config.WTF_CSRF_ENABLED)

    def test_segredos_sao_diferentes(self):
        """Testa que SESSION_SECRET e JWT_SECRET_KEY são diferentes"""
        from app.config import Config
        config = Config()
        self.assertNotEqual(config.JWT_SECRET_KEY, config.SECRET_KEY)

    def test_cookie_httponly_ativo(self):
        """Testa que SESSION_COOKIE_HTTPONLY está ativo"""
        from app.config import Config
        config = Config()
        self.assertTrue(config.SESSION_COOKIE_HTTPONLY)

    def test_cookie_samesite_configurado(self):
        """Testa que SESSION_COOKIE_SAMESITE está configurado"""
        from app.config import Config
        config = Config()
        self.assertIsNotNone(config.SESSION_COOKIE_SAMESITE)
        self.assertEqual(config.SESSION_COOKIE_SAMESITE, 'Lax')

    def test_segredos_tamanho_minimo(self):
        """Testa que segredos têm pelo menos 32 caracteres"""
        from app.config import Config
        config = Config()
        self.assertGreaterEqual(len(config.SECRET_KEY), 32)
        self.assertGreaterEqual(len(config.JWT_SECRET_KEY), 32)


if __name__ == '__main__':
    unittest.main(verbosity=2)
