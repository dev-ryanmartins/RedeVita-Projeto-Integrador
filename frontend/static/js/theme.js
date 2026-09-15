/* Preferências globais de visualização: Tema Claro/Escuro, Alto Contraste, Tamanho de Fonte e PWA. */
(function () {
    'use strict';

    if (window.__REDEVITA_THEME_INITIALIZED__) {
        return;
    }
    window.__REDEVITA_THEME_INITIALIZED__ = true;

    const THEME_KEY = 'redevita-theme';
    const FONT_SCALE_KEY = 'redevita-font-scale';
    const CONTRAST_KEY = 'redevita-contrast';
    const READING_KEY = 'redevita-reading';
    const root = document.documentElement;

    function readStorage(key) {
        try {
            return window.localStorage.getItem(key);
        } catch (error) {
            return null;
        }
    }

    function writeStorage(key, value) {
        try {
            window.localStorage.setItem(key, value);
        } catch (error) {
            // Navegadores em modo anônimo podem restringir localStorage
        }
    }

    function removeStorage(key) {
        try {
            window.localStorage.removeItem(key);
        } catch (error) {}
    }

    function systemTheme() {
        return window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches
            ? 'light'
            : 'dark';
    }

    // ==========================================
    // 1. TEMA CLARO / ESCURO
    // ==========================================
    function applyTheme(theme, persist) {
        const selectedTheme = (theme === 'light' || theme === 'dark') ? theme : 'dark';
        const isLight = selectedTheme === 'light';

        root.classList.toggle('light-theme', isLight);
        root.classList.toggle('dark-theme', !isLight);
        root.dataset.theme = selectedTheme;
        root.style.colorScheme = selectedTheme;

        if (document.body) {
            document.body.classList.toggle('light-theme', isLight);
            document.body.classList.toggle('dark-theme', !isLight);
            document.body.dataset.theme = selectedTheme;
        }

        if (persist) {
            writeStorage(THEME_KEY, selectedTheme);
        }
        updateThemeControls(selectedTheme);
    }

    function updateThemeControls(theme) {
        const isLight = theme === 'light';
        const label = isLight ? 'Ativar modo escuro' : 'Ativar modo claro';

        document.querySelectorAll('[data-theme-toggle]').forEach((button) => {
            const icon = button.querySelector('[data-theme-icon]');
            button.setAttribute('aria-label', label);
            button.setAttribute('title', label);
            button.setAttribute('aria-pressed', String(isLight));
            button.dataset.tooltip = label;
            if (icon) {
                icon.className = isLight ? 'ph-duotone ph-moon' : 'ph-duotone ph-sun';
            }
        });

        const toggleText = document.getElementById('themeToggleText');
        if (toggleText) {
            toggleText.textContent = isLight ? 'Modo Escuro' : 'Modo Claro';
        }
    }

    function toggleTheme() {
        const isCurrentlyLight = root.classList.contains('light-theme') || root.dataset.theme === 'light';
        const nextTheme = isCurrentlyLight ? 'dark' : 'light';
        applyTheme(nextTheme, true);
    }

    // ==========================================
    // 2. TAMANHO DA FONTE
    // ==========================================
    function applyFontScale(scale, persist) {
        const selectedScale = ['normal', 'large', 'xlarge'].includes(scale) ? scale : 'normal';
        root.classList.remove('font-large', 'font-xlarge');
        if (selectedScale !== 'normal') {
            root.classList.add(`font-${selectedScale}`);
        }
        root.dataset.fontScale = selectedScale;

        if (document.body) {
            document.body.classList.remove('font-large', 'font-xlarge');
            if (selectedScale !== 'normal') {
                document.body.classList.add(`font-${selectedScale}`);
            }
        }

        if (persist) {
            writeStorage(FONT_SCALE_KEY, selectedScale);
        }
        updateFontControls(selectedScale);
    }

    function updateFontControls(scale) {
        const sizes = { normal: 0, large: 1, xlarge: 2 };
        const current = sizes[scale] ?? 0;

        document.querySelectorAll('[data-font-increase]').forEach((button) => {
            button.disabled = current >= sizes.xlarge;
            button.setAttribute('aria-disabled', String(button.disabled));
        });
        document.querySelectorAll('[data-font-decrease]').forEach((button) => {
            button.disabled = current <= sizes.normal;
            button.setAttribute('aria-disabled', String(button.disabled));
        });

        document.querySelectorAll('[data-font-set]').forEach((button) => {
            const btnScale = button.getAttribute('data-font-set');
            if (btnScale === scale) {
                button.classList.add('btn-a11y-active');
            } else {
                button.classList.remove('btn-a11y-active');
            }
        });
    }

    // ==========================================
    // 3. ALTO CONTRASTE
    // ==========================================
    function applyContrast(isHigh, persist) {
        root.classList.toggle('high-contrast', isHigh);
        if (document.body) {
            document.body.classList.toggle('high-contrast', isHigh);
        }

        if (persist) {
            writeStorage(CONTRAST_KEY, isHigh ? 'high' : 'normal');
        }

        const contrastBtn = document.getElementById('btnHighContrastToggle');
        const contrastText = document.getElementById('contrastToggleText');
        if (contrastBtn) {
            contrastBtn.classList.toggle('btn-a11y-active', isHigh);
        }
        if (contrastText) {
            contrastText.textContent = isHigh ? 'Alto Contraste Ativo' : 'Alto Contraste';
        }
    }

    function toggleContrast() {
        const isCurrentHigh = root.classList.contains('high-contrast');
        applyContrast(!isCurrentHigh, true);
    }

    // ==========================================
    // 4. LEITURA SIMPLIFICADA
    // ==========================================
    function applyReadingMode(isActive, persist) {
        root.classList.toggle('reading-simplified', isActive);
        if (document.body) {
            document.body.classList.toggle('reading-simplified', isActive);
        }

        if (persist) {
            writeStorage(READING_KEY, isActive ? 'active' : 'inactive');
        }

        const readingBtn = document.getElementById('btnReadingToggle');
        const readingText = document.getElementById('readingToggleText');
        if (readingBtn) {
            readingBtn.classList.toggle('btn-a11y-active', isActive);
        }
        if (readingText) {
            readingText.textContent = isActive ? 'Ativado' : 'Ativar';
        }
    }

    function toggleReadingMode() {
        const isCurrent = root.classList.contains('reading-simplified');
        applyReadingMode(!isCurrent, true);
    }

    // ==========================================
    // 5. REDEFINIR PREFERÊNCIAS
    // ==========================================
    function resetPreferences() {
        removeStorage(THEME_KEY);
        removeStorage(FONT_SCALE_KEY);
        removeStorage(CONTRAST_KEY);
        removeStorage(READING_KEY);

        applyTheme('dark', false);
        applyFontScale('normal', false);
        applyContrast(false, false);
        applyReadingMode(false, false);
    }

    // ==========================================
    // INICIALIZAÇÃO IMEDIATA (Antes da renderização da página)
    // ==========================================
    const savedTheme = readStorage(THEME_KEY);
    const initialTheme = savedTheme ? savedTheme : 'dark';
    applyTheme(initialTheme, false);

    const savedScale = readStorage(FONT_SCALE_KEY);
    applyFontScale(savedScale || 'normal', false);

    const savedContrast = readStorage(CONTRAST_KEY);
    applyContrast(savedContrast === 'high', false);

    const savedReading = readStorage(READING_KEY);
    applyReadingMode(savedReading === 'active', false);

    // ==========================================
    // PWA - PROMPT DE INSTALAÇÃO NATIVO
    // ==========================================
    let deferredInstallPrompt = null;
    window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault();
        deferredInstallPrompt = e;
        const installBtn = document.getElementById('btnPWAInstall');
        if (installBtn) {
            installBtn.style.display = 'inline-flex';
        }
    });

    window.addEventListener('appinstalled', () => {
        deferredInstallPrompt = null;
        const installBtn = document.getElementById('btnPWAInstall');
        if (installBtn) {
            installBtn.style.display = 'none';
        }
    });

    // ==========================================
    // DELEGAÇÃO GLOBAL DE EVENTOS DE CLIQUE
    // ==========================================
    document.addEventListener('click', (e) => {
        // Alternar Tema
        const themeBtn = e.target.closest('[data-theme-toggle]');
        if (themeBtn) {
            e.preventDefault();
            toggleTheme();
            return;
        }

        // Aumentar Fonte
        const fontIncBtn = e.target.closest('[data-font-increase]');
        if (fontIncBtn) {
            e.preventDefault();
            const current = root.dataset.fontScale || 'normal';
            applyFontScale(current === 'normal' ? 'large' : 'xlarge', true);
            return;
        }

        // Diminuir Fonte
        const fontDecBtn = e.target.closest('[data-font-decrease]');
        if (fontDecBtn) {
            e.preventDefault();
            const current = root.dataset.fontScale || 'normal';
            applyFontScale(current === 'xlarge' ? 'large' : 'normal', true);
            return;
        }

        // Selecionar tamanho de fonte específico
        const fontSetBtn = e.target.closest('[data-font-set]');
        if (fontSetBtn) {
            e.preventDefault();
            const targetScale = fontSetBtn.getAttribute('data-font-set');
            applyFontScale(targetScale, true);
            return;
        }

        // Alternar Alto Contraste
        const contrastBtn = e.target.closest('[data-contrast-toggle]');
        if (contrastBtn) {
            e.preventDefault();
            toggleContrast();
            return;
        }

        // Alternar Leitura Simplificada
        const readingBtn = e.target.closest('[data-reading-toggle]');
        if (readingBtn) {
            e.preventDefault();
            toggleReadingMode();
            return;
        }

        // Abrir Modal de Acessibilidade
        const a11yToggle = e.target.closest('[data-a11y-toggle]');
        if (a11yToggle) {
            e.preventDefault();
            const modal = document.getElementById('accessibility-modal');
            if (modal) {
                const isVisible = modal.style.display === 'flex';
                modal.style.display = isVisible ? 'none' : 'flex';
                modal.setAttribute('aria-hidden', String(isVisible));
            }
            return;
        }

        // Fechar Modal de Acessibilidade
        const a11yClose = e.target.closest('[data-a11y-close]');
        if (a11yClose) {
            e.preventDefault();
            const modal = document.getElementById('accessibility-modal');
            if (modal) {
                modal.style.display = 'none';
                modal.setAttribute('aria-hidden', 'true');
            }
            return;
        }

        // Clicar fora do modal fecha o modal
        if (e.target.id === 'accessibility-modal') {
            e.target.style.display = 'none';
            e.target.setAttribute('aria-hidden', 'true');
            return;
        }

        // Redefinir Acessibilidade
        const resetBtn = e.target.closest('[data-a11y-reset]');
        if (resetBtn) {
            e.preventDefault();
            resetPreferences();
            return;
        }

        // Instalar PWA
        const pwaBtn = e.target.closest('#btnPWAInstall');
        if (pwaBtn) {
            e.preventDefault();
            if (deferredInstallPrompt) {
                deferredInstallPrompt.prompt();
                deferredInstallPrompt.userChoice.then((choiceResult) => {
                    if (choiceResult.outcome === 'accepted') {
                        console.log('Usuário aceitou a instalação do PWA');
                    }
                    deferredInstallPrompt = null;
                });
            } else {
                const pwaMsg = 'Para instalar o RedeVita: no Chrome/Edge clique no ícone de instalação na barra de endereços; no celular selecione "Adicionar à tela inicial".';
                if (window.showToast) {
                    window.showToast(pwaMsg, 'info', 6000, 'Instalação do App');
                } else {
                    alert(pwaMsg);
                }
            }
            return;
        }
    });

    // Atualiza controles assim que o DOM estiver pronto
    function syncUI() {
        updateThemeControls(root.dataset.theme || initialTheme);
        updateFontControls(root.dataset.fontScale || 'normal');
        applyContrast(root.classList.contains('high-contrast'), false);
        applyReadingMode(root.classList.contains('reading-simplified'), false);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', syncUI);
    } else {
        syncUI();
    }
})();
