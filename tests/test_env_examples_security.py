"""
Testes para P1.13: Verifica que arquivos de exemplo não contêm tokens preenchidos
"""

import os
import pytest


@pytest.fixture
def env_example_path():
    """Caminho para o arquivo .env.example."""
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.example')


@pytest.fixture
def env_docker_example_path():
    """Caminho para o arquivo .env.docker.example."""
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.docker.example')


class TestEnvExamplesSecurity:
    """Testes de segurança de arquivos de exemplo."""
    
    def test_anvisa_api_token_vazio_em_env_example(self, env_example_path):
        """ANVISA_API_TOKEN está vazio em .env.example."""
        with open(env_example_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        for line in lines:
            if 'ANVISA_API_TOKEN=' in line and not line.strip().startswith('#'):
                key, value = line.split('=', 1)
                # Valor deve estar vazio
                assert value == '', f"ANVISA_API_TOKEN deve estar vazio em .env.example, encontrado: '{value}'"
    
    def test_anvisa_api_token_vazio_em_env_docker_example(self, env_docker_example_path):
        """ANVISA_API_TOKEN está vazio em .env.docker.example."""
        with open(env_docker_example_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        for line in lines:
            if 'ANVISA_API_TOKEN=' in line and not line.strip().startswith('#'):
                key, value = line.split('=', 1)
                # Valor deve estar vazio
                assert value == '', f"ANVISA_API_TOKEN deve estar vazio em .env.docker.example, encontrado: '{value}'"
    
    def test_google_maps_api_key_vazio_em_env_example(self, env_example_path):
        """GOOGLE_MAPS_API_KEY está vazio em .env.example."""
        with open(env_example_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        for line in lines:
            if 'GOOGLE_MAPS_API_KEY=' in line and not line.strip().startswith('#'):
                key, value = line.split('=', 1)
                # Valor deve estar vazio
                assert value == '', f"GOOGLE_MAPS_API_KEY deve estar vazio em .env.example, encontrado: '{value}'"
    
    def test_google_maps_api_key_vazio_em_env_docker_example(self, env_docker_example_path):
        """GOOGLE_MAPS_API_KEY está vazio em .env.docker.example."""
        with open(env_docker_example_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        for line in lines:
            if 'GOOGLE_MAPS_API_KEY=' in line and not line.strip().startswith('#'):
                key, value = line.split('=', 1)
                # Valor deve estar vazio
                assert value == '', f"GOOGLE_MAPS_API_KEY deve estar vazio em .env.docker.example, encontrado: '{value}'"
    
    def test_secret_keys_vazios_em_env_example(self, env_example_path):
        """SECRET_KEY e JWT_SECRET_KEY estão vazios em .env.example."""
        with open(env_example_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        for line in lines:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.split('=', 1)
                # Para chaves de segredo, valor deve estar vazio
                if 'SECRET_KEY' in key or 'JWT_SECRET_KEY' in key:
                    assert value == '', f"{key} deve estar vazio em .env.example, encontrado: '{value}'"
    
    def test_secret_keys_vazios_em_env_docker_example(self, env_docker_example_path):
        """SECRET_KEY e JWT_SECRET_KEY estão vazios em .env.docker.example."""
        with open(env_docker_example_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        for line in lines:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.split('=', 1)
                # Para chaves de segredo, valor deve estar vazio
                if 'SECRET_KEY' in key or 'JWT_SECRET_KEY' in key:
                    assert value == '', f"{key} deve estar vazio em .env.docker.example, encontrado: '{value}'"
    
    def test_mysql_passwords_vazios_em_env_example(self, env_example_path):
        """MYSQL_ROOT_PASSWORD e MYSQL_PASSWORD estão vazios em .env.example."""
        with open(env_example_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        for line in lines:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.split('=', 1)
                # Para senhas de MySQL, valor deve estar vazio
                if 'MYSQL_PASSWORD' in key:
                    assert value == '', f"{key} deve estar vazio em .env.example, encontrado: '{value}'"
    
    def test_mysql_passwords_vazios_em_env_docker_example(self, env_docker_example_path):
        """MYSQL_ROOT_PASSWORD e MYSQL_PASSWORD estão vazios em .env.docker.example."""
        with open(env_docker_example_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        for line in lines:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.split('=', 1)
                # Para senhas de MySQL, valor deve estar vazio
                if 'MYSQL_PASSWORD' in key:
                    assert value == '', f"{key} deve estar vazio em .env.docker.example, encontrado: '{value}'"
    
    def test_nao_ha_valores_preenchidos_que_parecam_tokens(self, env_example_path):
        """Arquivos de exemplo não contêm valores que pareçam tokens reais."""
        with open(env_example_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        for line in lines:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.split('=', 1)
                # Valor não deve ter mais de 20 caracteres (indica potencialmente um token real)
                # Exceto para valores não sensíveis como PORT ou DATABASE
                sensitive_keys = ['SECRET_KEY', 'JWT_SECRET_KEY', 'MYSQL_PASSWORD', 
                               'ANVISA_API_TOKEN', 'GOOGLE_MAPS_API_KEY', 'DATABASE_URL']
                if any(sensitive_key in key for sensitive_key in sensitive_keys):
                    if value and len(value) > 20:
                        pytest.fail(f"Valor em {key} parece ser um token real ({len(value)} caracteres)")
