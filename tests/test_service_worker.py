"""
Testes para P2.1: Verifica registro do service worker e restrições de cache
"""

import os
import pytest


class TestServiceWorkerRegistration:
    """Testes para registro do service worker."""
    
    def test_service_worker_file_exists(self):
        """Arquivo sw.js existe em frontend/static/."""
        sw_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'static', 'sw.js')
        assert os.path.exists(sw_path), "Arquivo sw.js não encontrado"
    
    def test_service_worker_registrado_no_theme_js(self):
        """theme.js contém código para registrar o service worker."""
        theme_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'static', 'js', 'theme.js')
        
        with open(theme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Deve conter navigator.serviceWorker.register
        assert 'navigator.serviceWorker.register' in content
        # Deve verificar contexto seguro
        assert 'https:' in content or 'localhost' in content
        # Deve tratar erros de registro
        assert 'catch' in content
        # Deve registrar /static/sw.js
        assert '/static/sw.js' in content
    
    def test_service_worker_verifica_contexto_seguro(self):
        """Registro do service worker verifica contexto seguro (HTTPS ou localhost)."""
        theme_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'static', 'js', 'theme.js')
        
        with open(theme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Deve verificar protocolo
        assert 'window.location.protocol' in content
        # Deve verificar hostname
        assert 'window.location.hostname' in content
        # Deve permitir localhost
        assert 'localhost' in content
        # Deve permitir 127.0.0.1
        assert '127.0.0.1' in content
    
    def test_service_worker_trata_falha_sem_quebrar_pagina(self):
        """Falha de registro não quebra a aplicação."""
        theme_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'static', 'js', 'theme.js')
        
        with open(theme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Deve usar try-catch no registro
        assert 'try' in content
        assert 'catch' in content
        # Deve logar erro sem expor detalhes internos
        assert 'console.log' in content or 'console.warn' in content
        # Não deve usar alert em caso de falha
        if 'serviceWorker' in content:
            sw_index = content.index('serviceWorker')
            sw_section = content[sw_index:sw_index+200]
            assert 'alert' not in sw_section.lower()


class TestServiceWorkerCacheRestrictions:
    """Testes para restrições de cache do service worker."""
    
    def test_sw_nao_cachear_html_root(self):
        """sw.js não deve cachear '/' (página raiz) sozinho."""
        sw_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'static', 'sw.js')
        
        with open(sw_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # STATIC_ASSETS não deve conter '/' sozinho (página raiz)
        if 'STATIC_ASSETS' in content:
            static_start = content.index('STATIC_ASSETS')
            static_end = content.index(']', static_start)
            static_section = content[static_start:static_end]
            # '/' pode estar em caminhos como '/static/', mas não sozinho
            # Verificar que não há '/' sozinho na lista
            lines = static_section.split('\n')
            for line in lines:
                if '/' in line and "'/" in line:
                    # Verificar se tem mais caminho após a barra
                    if len(line.strip().split("'/")[1].split("'")[0]) > 0:
                        # Tem caminho após a barra, não é página raiz
                        pass
                    else:
                        pytest.fail("STATIC_ASSETS contém '/' como página raiz")
    
    def test_sw_nao_cachear_rotas_api(self):
        """sw.js não deve cachear rotas de API (/api/)."""
        sw_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'static', 'sw.js')
        
        with open(sw_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Deve ter verificação para /api/
        assert '/api/' in content
        # Deve usar fetch direto para /api/
        assert 'fetch(event.request)' in content
    
    def test_sw_nao_cachear_login_register(self):
        """sw.js não deve cachear rotas de login/registro."""
        sw_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'static', 'sw.js')
        
        with open(sw_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Deve ter verificação para /login ou /register
        assert '/login' in content or '/register' in content
    
    def test_sw_nao_cachear_navegacao_html(self):
        """sw.js não deve cachear navegação HTML (navigate mode)."""
        sw_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'static', 'sw.js')
        
        with open(sw_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Deve ter verificação para navigate mode
        assert 'navigate' in content
        # Deve usar fetch direto para navigate
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'navigate' in line:
                # Verificar que não há cache.match nas próximas linhas
                next_lines = '\n'.join(lines[i:i+10])
                assert 'caches.match' not in next_lines or 'fetch(event.request)' in next_lines
    
    def test_sw_cachear_apenas_estaticos(self):
        """sw.js deve cachear apenas /static/."""
        sw_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'static', 'sw.js')
        
        with open(sw_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Deve ter verificação para /static/
        assert '/static/' in content
        # Deve usar Cache First para /static/
        assert 'caches.match' in content
    
    def test_sw_limpeza_cache_versoes_antigas(self):
        """sw.js deve limpar caches de versões antigas."""
        sw_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'static', 'sw.js')
        
        with open(sw_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Deve ter listener 'activate'
        assert "addEventListener('activate'" in content
        # Deve deletar caches diferentes de CACHE_NAME
        assert 'caches.delete' in content
        # Deve usar filter para keys diferentes
        assert 'filter' in content
    
    def test_sw_nao_exclui_dados_alheios(self):
        """sw.js não deve apagar dados alheios ao service worker."""
        sw_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'static', 'sw.js')
        
        with open(sw_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Deve apagar apenas caches com nome diferente de CACHE_NAME
        assert 'key !== CACHE_NAME' in content
        # Deve usar filter antes de deletar
        assert 'filter' in content


class TestServiceWorkerContentSensitivity:
    """Testes para conteúdo sensível não ser armazenado em cache."""
    
    def test_sw_static_assets_publicos(self):
        """STATIC_ASSETS contém apenas recursos públicos não sensíveis."""
        sw_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'static', 'sw.js')
        
        with open(sw_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extrair STATIC_ASSETS
        start = content.index('STATIC_ASSETS = [')
        end = content.index(']', start)
        assets = content[start:end+1]
        
        # Não deve conter rotas de API
        assert '/api/' not in assets
        # Não deve conter login (como rota, não em nome de arquivo)
        assert "'/login'" not in assets
        # Não deve conter receitas (dados clínicos)
        assert 'receita' not in assets.lower()
        # Não deve conter perfil (como rota, não em nome de arquivo)
        assert "'/perfil'" not in assets
        # CSS e JS são aceitáveis, mesmo com nomes de páginas
    
    def test_sw_cache_first_apenas_estaticos(self):
        """Cache First é aplicado apenas para /static/."""
        sw_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'static', 'sw.js')
        
        with open(sw_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        in_static_check = False
        has_cache_first_static = False
        
        for line in lines:
            if '/static/' in line:
                in_static_check = True
            if in_static_check and 'caches.match' in line:
                has_cache_first_static = True
            if in_static_check and 'return' in line:
                in_static_check = False
        
        assert has_cache_first_static, "Cache First não está sendo aplicado para /static/"
