"""
Testes para P1.10: Verifica que docker-compose.yml não contém segredos e a porta do banco está restrita
"""

import os
import pytest


@pytest.fixture
def docker_compose_path():
    """Caminho para o arquivo docker-compose.yml."""
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docker-compose.yml')


@pytest.fixture
def env_example_path():
    """Caminho para o arquivo .env.example."""
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.example')


@pytest.fixture
def env_docker_example_path():
    """Caminho para o arquivo .env.docker.example."""
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.docker.example')


class TestDockerComposeSecurity:
    """Testes de segurança do Docker Compose."""
    
    def test_docker_compose_nao_contem_segredos_hardcoded(self, docker_compose_path):
        """docker-compose.yml não contém segredos hardcoded."""
        with open(docker_compose_path, 'r') as f:
            content = f.read()
        
        # Não deve conter credenciais hardcoded (valores reais, não nomes de variáveis)
        hardcoded_secrets = [
            'root123', 'redevita123', 'redevita_projeto_ads_2026',
            'redevita_jwt_secret_2026', 'redevita-secret-key-change-in-production',
            'zGBqdEtg0wq9SrLTa90j3yLb8El784tK', 'AIzaSyB-ANEs_OI2FkfhdPK2UwOuY998IlwsXEQ'
        ]
        
        for secret in hardcoded_secrets:
            assert secret not in content, f"Segredo potencialmente hardcoded encontrado: {secret}"
        
        # Não deve ter DATABASE_URL com credenciais hardcoded
        # Deve usar variável de ambiente
        if 'DATABASE_URL=mysql+pymysql://' in content:
            # Se tiver a URL hardcoded, deve usar apenas variáveis
            assert 'redevita:redevita123' not in content, "DATABASE_URL não deve ter credenciais hardcoded"
    
    def test_docker_compose_usa_variaveis_ambiente(self, docker_compose_path):
        """docker-compose.yml usa variáveis de ambiente para segredos."""
        with open(docker_compose_path, 'r') as f:
            content = f.read()
        
        # Deve usar ${VARIABLE} para segredos
        assert '${DATABASE_URL}' in content or '$DATABASE_URL' in content
        assert '${SECRET_KEY}' in content or '$SECRET_KEY' in content
        assert '${JWT_SECRET_KEY}' in content or '$JWT_SECRET_KEY' in content
        assert '${MYSQL_ROOT_PASSWORD}' in content or '$MYSQL_ROOT_PASSWORD' in content
        assert '${MYSQL_PASSWORD}' in content or '$MYSQL_PASSWORD' in content
    
    def test_porta_mysql_restrita_localhost(self, docker_compose_path):
        """Porta do MySQL está restrita a localhost (127.0.0.1)."""
        with open(docker_compose_path, 'r') as f:
            content = f.read()
        
        # Deve ter "127.0.0.1:3306" ou não publicar a porta
        assert '127.0.0.1:3306' in content or '3306:3306' not in content
    
    def test_porta_mysql_nao_publica_globalmente(self, docker_compose_path):
        """Porta do MySQL não está publicada globalmente (sem restrição de IP)."""
        with open(docker_compose_path, 'r') as f:
            content = f.read()
        
        # Não deve ter apenas "3306:3306" (publica em todas as interfaces)
        lines = content.split('\n')
        for line in lines:
            if '3306:3306' in line and '127.0.0.1' not in line:
                pytest.fail(f"Porta MySQL publicada globalmente: {line.strip()}")
    
    def test_env_example_nao_contem_segredos_reais(self, env_example_path):
        """.env.example não contém segredos reais."""
        with open(env_example_path, 'r') as f:
            content = f.read()
        
        # Valores de segredos devem estar vazios ou ser placeholders óbvios
        # Valores não sensíveis (como PORT, DATABASE) podem ter valores de exemplo
        secret_keys = ['SECRET_KEY', 'DATABASE_URL', 'JWT_SECRET_KEY', 'MYSQL_ROOT_PASSWORD', 
                       'MYSQL_PASSWORD', 'MYSQL_USER', 'ANVISA_API_TOKEN', 'GOOGLE_MAPS_API_KEY']
        
        lines = content.split('\n')
        for line in lines:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.split('=', 1)
                # Para chaves de segredo, valor deve estar vazio ou ser placeholder
                if any(secret_key in key for secret_key in secret_keys):
                    assert value == '' or 'change' in value.lower() or 'placeholder' in value.lower() or 'example' in value.lower(), \
                        f"Valor potencialmente real em .env.example: {key}={value}"
    
    def test_env_docker_example_nao_contem_segredos_reais(self, env_docker_example_path):
        """.env.docker.example não contém segredos reais."""
        with open(env_docker_example_path, 'r') as f:
            content = f.read()
        
        # Valores de segredos devem estar vazios ou ser placeholders óbvios
        # Valores não sensíveis (como DATABASE, FLASK_ENV) podem ter valores de exemplo
        secret_keys = ['MYSQL_ROOT_PASSWORD', 'MYSQL_PASSWORD', 'MYSQL_USER', 
                       'SECRET_KEY', 'DATABASE_URL', 'JWT_SECRET_KEY', 
                       'ANVISA_API_TOKEN', 'GOOGLE_MAPS_API_KEY']
        
        lines = content.split('\n')
        for line in lines:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.split('=', 1)
                # Para chaves de segredo, valor deve estar vazio ou ser placeholder
                if any(secret_key in key for secret_key in secret_keys):
                    assert value == '' or 'change' in value.lower() or 'placeholder' in value.lower() or 'example' in value.lower(), \
                        f"Valor potencialmente real em .env.docker.example: {key}={value}"
    
    def test_docker_compose_yaml_valido(self, docker_compose_path):
        """docker-compose.yml é um YAML válido (verificação básica)."""
        with open(docker_compose_path, 'r') as f:
            content = f.read()
        
        # Verificação básica de estrutura YAML
        assert 'version:' in content
        assert 'services:' in content
        assert 'web:' in content
        assert 'db:' in content
    
    def test_servicos_usam_rede_privada_compose(self, docker_compose_path):
        """Serviços usam a rede privada do Compose para comunicação interna."""
        with open(docker_compose_path, 'r') as f:
            content = f.read()
        
        # DATABASE_URL deve usar variável de ambiente (que aponta para 'db')
        # Não deve ter hardcoded @localhost ou @127.0.0.1 para o banco
        # Se tiver DATABASE_URL hardcoded, deve usar @db:
        if 'DATABASE_URL=mysql+pymysql://' in content:
            assert '@db:' in content, \
                "DATABASE_URL hardcoded deve usar hostname 'db' (rede privada do Compose)"
