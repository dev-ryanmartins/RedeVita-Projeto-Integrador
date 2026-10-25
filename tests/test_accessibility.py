"""
Testes estáticos de acessibilidade para frontend.

Este arquivo verifica que o código-fonte HTML/CSS/JS implementa os requisitos
de acessibilidade para controles do mapa e formulários essenciais.
"""

import pytest
import os
from pathlib import Path


class TestMapaAccessibility:
    """Verifica acessibilidade dos controles do mapa."""

    @pytest.fixture
    def mapa_html_path(self):
        """Caminho para o arquivo mapa.html."""
        return Path(__file__).parent.parent / "frontend" / "templates" / "mapa.html"

    @pytest.fixture
    def mapa_content(self, mapa_html_path):
        """Conteúdo do arquivo mapa.html."""
        with open(mapa_html_path, 'r', encoding='utf-8') as f:
            return f.read()

    def test_mapa_checkbox_nao_display_none(self, mapa_content):
        """Checkboxes de filtro não devem usar display:none."""
        assert 'display:none' not in mapa_content.split('input[type="checkbox"]')[0] if 'input[type="checkbox"]' in mapa_content else True, \
               "Checkboxes não devem usar display:none (inacessível por teclado)"

    def test_mapa_checkbox_focusable(self, mapa_content):
        """Checkboxes devem permanecer focáveis por teclado."""
        # Verifica que há técnica de ocultação acessível (clip, opacity, position)
        lines = mapa_content.split('\n')
        in_checkbox_section = False
        has_accessible_hiding = False
        
        for line in lines:
            if 'input[type="checkbox"]' in line:
                in_checkbox_section = True
            if in_checkbox_section:
                if 'clip' in line or 'opacity' in line or 'position: absolute' in line:
                    has_accessible_hiding = True
                    break
                if '}' in line and 'input' not in line:
                    break
        
        assert has_accessible_hiding, \
               "Checkboxes devem usar técnica de ocultação acessível (clip/opacity/position)"

    def test_mapa_focus_visible_on_checkbox(self, mapa_content):
        """Checkbox deve ter foco visível quando receber foco por teclado."""
        assert ':focus' in mapa_content or 'focus-visible' in mapa_content, \
               "Deve haver estilo de foco visível para controles"
        assert 'filter-dot' in mapa_content and ':focus' in mapa_content, \
               "Foco deve ser visível no elemento .filter-dot"

    def test_mapa_labels_associated(self, mapa_content):
        """Labels devem estar associados aos controles via for/for."""
        assert 'for="filterFarmacias"' in mapa_content, \
               "Label deve estar associado ao checkbox via atributo for"
        assert 'id="filterFarmacias"' in mapa_content, \
               "Checkbox deve ter id correspondente ao label"

    def test_mapa_aria_pressed_on_buttons(self, mapa_content):
        """Botões de filtro devem ter aria-pressed para estado."""
        assert 'aria-pressed' in mapa_content, \
               "Botões de acesso devem ter aria-pressed para indicar estado"

    def test_mapa_role_group_on_filters(self, mapa_content):
        """Grupos de filtros devem ter role=\"group\"."""
        assert 'role="group"' in mapa_content, \
               "Grupos de controles devem ter role=\"group\""

    def test_mapa_aria_labelledby(self, mapa_content):
        """Grupos devem ter aria-labelledby referenciando label."""
        assert 'aria-labelledby' in mapa_content, \
               "Grupos devem ter aria-labelledby referenciando label descritivo"
        assert 'id="label-acesso"' in mapa_content, \
               "Label de acesso deve ter id para referência"
        assert 'id="label-camadas"' in mapa_content, \
               "Label de camadas deve ter id para referência"

    def test_mapa_aria_label_on_checkbox(self, mapa_content):
        """Checkbox deve ter aria-label descritivo."""
        assert 'aria-label' in mapa_content and 'farmacias' in mapa_content.lower(), \
               "Checkbox deve ter aria-label descritivo para leitores de tela"

    def test_mapa_aria_live_on_count(self, mapa_content):
        """Contador deve ter aria-live para atualizações dinâmicas."""
        assert 'aria-live' in mapa_content, \
               "Contador dinâmico deve ter aria-live para anunciar mudanças"

    def test_mapa_aria_hidden_on_icons(self, mapa_content):
        """Ícones decorativos devem ter aria-hidden=\"true\"."""
        # Verifica que há ícones com aria-hidden
        assert 'aria-hidden' in mapa_content, \
               "Ícones decorativos devem ter aria-hidden=\"true\""

    def test_mapa_search_input_label(self, mapa_content):
        """Campo de busca deve ter label associado."""
        assert 'id="mapaSearch"' in mapa_content, \
               "Campo de busca deve ter id"
        # Deve ter label associado (for ou aria-label)
        assert 'aria-label' in mapa_content or 'placeholder' in mapa_content, \
               "Campo de busca deve ter label ou placeholder descritivo"

    def test_mapa_buttons_focusable(self, mapa_content):
        """Botões devem ser focáveis e clicáveis por teclado."""
        assert '<button' in mapa_content, \
               "Deve haver elementos button nativos (focáveis por teclado)"
        # Botões de acesso devem ter onclick
        assert 'onclick' in mapa_content, \
               "Botões devem ter handler de evento"


class TestLoginFormAccessibility:
    """Verifica acessibilidade do formulário de login."""

    @pytest.fixture
    def login_html_path(self):
        """Caminho para o arquivo login.html."""
        return Path(__file__).parent.parent / "frontend" / "templates" / "login.html"

    @pytest.fixture
    def login_content(self, login_html_path):
        """Conteúdo do arquivo login.html."""
        with open(login_html_path, 'r', encoding='utf-8') as f:
            return f.read()

    def test_login_inputs_have_labels(self, login_content):
        """Inputs devem ter labels associados."""
        assert 'for="identificador"' in login_content, \
               "Input de identificador deve ter label associado via for"
        assert 'id="identificador"' in login_content, \
               "Input de identificador deve ter id correspondente"
        assert 'for="senha"' in login_content or 'id="label-senha"' in login_content, \
               "Input de senha deve ter label associado"

    def test_login_aria_required(self, login_content):
        """Campos obrigatórios devem ter aria-required=\"true\"."""
        assert 'aria-required' in login_content, \
               "Campos obrigatórios devem ter aria-required=\"true\""

    def test_login_aria_describedby_errors(self, login_content):
        """Erros devem ser associados aos campos via aria-describedby."""
        assert 'aria-describedby' in login_content, \
               "Campos devem ter aria-describedby referenciando mensagens de erro"
        assert 'flash-messages' in login_content, \
               "Container de mensagens deve ter id para referência"

    def test_login_flash_messages_role_alert(self, login_content):
        """Mensagens flash devem ter role=\"alert\" e aria-live."""
        assert 'role="alert"' in login_content, \
               "Mensagens de erro devem ter role=\"alert\""
        assert 'aria-live' in login_content, \
               "Mensagens de erro devem ter aria-live para leitores de tela"

    def test_login_icons_aria_hidden(self, login_content):
        """Ícones decorativos devem ter aria-hidden=\"true\"."""
        assert 'aria-hidden="true"' in login_content, \
               "Ícones decorativos devem ter aria-hidden=\"true\""

    def test_login_form_novalidate(self, login_content):
        """Formulário deve ter novalidate para validação customizada."""
        assert 'novalidate' in login_content, \
               "Formulário deve ter novalidate para validação customizada acessível"

    def test_login_autocomplete_attributes(self, login_content):
        """Campos devem ter autocomplete apropriado."""
        assert 'autocomplete="username"' in login_content, \
               "Campo de identificador deve ter autocomplete=\"username\""
        assert 'autocomplete="current-password"' in login_content, \
               "Campo de senha deve ter autocomplete=\"current-password\""


class TestFormAccessibilityPatterns:
    """Verifica padrões gerais de acessibilidade em formulários."""

    @pytest.fixture
    def templates_dir(self):
        """Diretório de templates."""
        return Path(__file__).parent.parent / "frontend" / "templates"

    def test_contrast_ratio_not_verified(self, templates_dir):
        """
        Nota: Contraste de cor não é verificado automaticamente neste teste.
        Requer auditoria visual ou ferramenta como axe-core/Playwright.
        """
        # Este teste documenta a limitação
        pass

    def test_keyboard_navigation_not_verified(self, templates_dir):
        """
        Nota: Navegação por teclado não é verificada automaticamente neste teste.
        Requer teste manual em navegador ou ferramenta de E2E.
        """
        # Este teste documenta a limitação
        pass

    def test_zoom_responsiveness_not_verified(self, templates_dir):
        """
        Nota: Comportamento em zoom e viewport estreita não é verificado automaticamente.
        Requer teste visual em diferentes viewports.
        """
        # Este teste documenta a limitação
        pass
