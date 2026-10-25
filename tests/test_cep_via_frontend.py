"""
Testes estáticos para verificação de CEP ViaCEP no frontend.

Este arquivo verifica que o código-fonte JavaScript implementa os requisitos
para busca manual de CEP, sem fazer chamadas reais ao ViaCEP.
"""

import pytest
import os
from pathlib import Path


class TestCEPBuscaManual:
    """Verifica que a busca de CEP é manual e não automática."""

    @pytest.fixture
    def mascaras_js_path(self):
        """Caminho para o arquivo mascaras.js."""
        return Path(__file__).parent.parent / "frontend" / "static" / "js" / "mascaras.js"

    @pytest.fixture
    def mascaras_content(self, mascaras_js_path):
        """Conteúdo do arquivo mascaras.js."""
        with open(mascaras_js_path, 'r', encoding='utf-8') as f:
            return f.read()

    def test_cep_nao_dispara_no_blur(self, mascaras_content):
        """Sair do campo CEP não deve disparar consulta automaticamente."""
        # Verifica que não há 'blur' com fetch para ViaCEP
        assert 'addEventListener(\'blur\'' not in mascaras_content or \
               'viacep.com.br' not in mascaras_content.split('addEventListener(\'blur\'')[0] if 'addEventListener(\'blur\'' in mascaras_content else True, \
               "Consulta ViaCEP não deve ser disparada no evento blur"

    def test_cep_busca_manual_com_botao(self, mascaras_content):
        """Busca de CEP deve ser iniciada por botão explicitamente."""
        assert '.btn-buscar-cep' in mascaras_content, \
               "Deve haver um botão com classe .btn-buscar-cep para iniciar a busca"

    def test_cep_timeout_configurado(self, mascaras_content):
        """Consulta deve ter timeout configurado."""
        assert 'AbortSignal.timeout' in mascaras_content or 'setTimeout' in mascaras_content, \
               "Consulta ViaCEP deve ter timeout configurado"

    def test_cep_preserva_endereco_manual(self, mascaras_content):
        """Endereço digitado manualmente deve ser preservado se usuário editar."""
        assert 'enderecoOriginal' in mascaras_content, \
               "Deve armazenar valor original do endereço para proteção"
        assert 'enderecoAtual !== enderecoOriginal' in mascaras_content, \
               "Deve verificar se usuário editou endereço durante busca"

    def test_cep_mensagens_acessiveis(self, mascaras_content):
        """Mensagens de estado devem usar atributos ARIA."""
        assert 'aria-live' in mascaras_content, \
               "Mensagens devem usar aria-live para leitores de tela"
        assert 'role' in mascaras_content and 'alert' in mascaras_content, \
               "Mensagens de erro devem ter role='alert'"

    def test_cep_valida_tamanho(self, mascaras_content):
        """CEP deve ser validado antes da consulta."""
        assert 'cep.length !== 8' in mascaras_content or 'length === 8' in mascaras_content, \
               "CEP deve ter 8 dígitos para ser válido"

    def test_cep_trata_erro_http(self, mascaras_content):
        """Erros HTTP devem ser tratados sem quebrar o formulário."""
        assert 'response.ok' in mascaras_content or '!response.ok' in mascaras_content, \
               "Resposta HTTP deve ser verificada"
        assert 'catch' in mascaras_content, \
               "Erros devem ser capturados em try-catch"

    def test_cep_trata_timeout(self, mascaras_content):
        """Timeout deve ser tratado especificamente."""
        assert 'AbortError' in mascaras_content, \
               "Timeout deve ser tratado como AbortError"

    def test_cep_nao_loga_dados_sensiveis(self, mascaras_content):
        """CEP ou endereço não devem ser logados em detalhes."""
        # Verifica que console.log não contém CEP ou endereço
        lines = mascaras_content.split('\n')
        for line in lines:
            if 'console.log' in line or 'console.error' in line:
                # Não deve logar valor de CEP ou endereço
                assert 'cep.value' not in line, \
                       "Não deve logar valor de CEP"
                assert 'enderecoInput.value' not in line, \
                       "Não deve logar valor de endereço"

    def test_cep_campos_editaveis(self, mascaras_content):
        """Campos de endereço devem permanecer editáveis."""
        # Verifica que o campo de endereço não se torna readonly
        assert 'enderecoInput.readOnly' not in mascaras_content, \
               "Campo de endereço não deve se tornar readonly"
        # Verifica que o campo de endereço não se torna disabled
        # (apenas o botão de busca pode ser desabilitado durante a requisição)
        assert 'enderecoInput.disabled' not in mascaras_content, \
               "Campo de endereço não deve se tornar disabled"

    def test_cep_busca_opcional(self, mascaras_content):
        """Busca deve ser opcional, não obrigatória."""
        # Verifica que não há bloqueio de submit baseado em CEP
        assert 'preventDefault' not in mascaras_content or 'cep' not in mascaras_content.split('preventDefault')[0] if 'preventDefault' in mascaras_content else True, \
               "Formulário não deve ser bloqueado se CEP não for buscado"


class TestCEPIntegracaoTemplate:
    """Verifica que templates podem integrar botão de busca CEP."""

    def test_template_mascara_cep_class(self):
        """Deve haver classe mask-cep disponível para inputs de CEP."""
        mascaras_js_path = Path(__file__).parent.parent / "frontend" / "static" / "js" / "mascaras.js"
        with open(mascaras_js_path, 'r', encoding='utf-8') as f:
            content = f.read()
        assert '.mask-cep' in content, \
               "Deve haver seletor .mask-cep para inputs de CEP"

    def test_container_mensagem_cep_exemplo(self):
        """Documenta como adicionar container de mensagem CEP."""
        # Este teste documenta o comportamento esperado
        # O container deve ter id="cep-mensagem" para receber mensagens
        mascaras_js_path = Path(__file__).parent.parent / "frontend" / "static" / "js" / "mascaras.js"
        with open(mascaras_js_path, 'r', encoding='utf-8') as f:
            content = f.read()
        assert 'cep-mensagem' in content, \
               "Código deve referenciar container com id='cep-mensagem'"
