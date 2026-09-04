/* Preferências globais de visualização: tema e tamanho da fonte. */
(function () {
    'use strict';

    const THEME_KEY = 'redevita-theme';
    const FONT_SCALE_KEY = 'redevita-font-scale';
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
            // Navegadores em modo privado podem bloquear o localStorage.
        }
    }

    function systemTheme() {
        return window.matchMedia &&
            window.matchMedia('(prefers-color-scheme: light)').matches
            ? 'light'
            : 'dark';
    }

    function validTheme(theme) {
        return theme === 'light' || theme === 'dark';
    }

    function applyTheme(theme, persist) {
        const selectedTheme = validTheme(theme) ? theme : 'dark';
        root.classList.toggle('light-theme', selectedTheme === 'light');
        root.classList.toggle('dark-theme', selectedTheme === 'dark');
        root.dataset.theme = selectedTheme;

        if (persist) writeStorage(THEME_KEY, selectedTheme);
        updateThemeControls(selectedTheme);
    }

    function updateThemeControls(theme) {
        const isLight = theme === 'light';
        document.querySelectorAll('[data-theme-toggle]').forEach((button) => {
            const label = isLight ? 'Ativar modo escuro' : 'Ativar modo claro';
            const icon = button.querySelector('[data-theme-icon]');
            button.setAttribute('aria-label', label);
            button.setAttribute('title', label);
            button.setAttribute('aria-pressed', String(isLight));
            button.dataset.tooltip = label;
            if (icon) {
                icon.className = isLight
                    ? 'fas fa-moon'
                    : 'fas fa-sun';
            }
        });
    }

    function applyFontScale(scale, persist) {
        const selectedScale = ['normal', 'large', 'xlarge'].includes(scale)
            ? scale
            : 'normal';
        root.classList.remove('font-large', 'font-xlarge');
        if (selectedScale !== 'normal') {
            root.classList.add(`font-${selectedScale}`);
        }
        root.dataset.fontScale = selectedScale;
        if (persist) writeStorage(FONT_SCALE_KEY, selectedScale);
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
    }

    const storedTheme = readStorage(THEME_KEY);
    const initialTheme = validTheme(storedTheme) ? storedTheme : systemTheme();
    applyTheme(initialTheme, false);
    applyFontScale(readStorage(FONT_SCALE_KEY), false);

    if (window.matchMedia) {
        const mediaQuery = window.matchMedia('(prefers-color-scheme: light)');
        const followSystemTheme = () => {
            if (!validTheme(readStorage(THEME_KEY))) {
                applyTheme(systemTheme(), false);
            }
        };
        if (mediaQuery.addEventListener) {
            mediaQuery.addEventListener('change', followSystemTheme);
        } else if (mediaQuery.addListener) {
            mediaQuery.addListener(followSystemTheme);
        }
    }

    document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('[data-theme-toggle]').forEach((button) => {
            button.addEventListener('click', () => {
                const nextTheme = root.dataset.theme === 'light' ? 'dark' : 'light';
                applyTheme(nextTheme, true);
            });
        });
        document.querySelectorAll('[data-font-increase]').forEach((button) => {
            button.addEventListener('click', () => {
                const current = root.dataset.fontScale || 'normal';
                applyFontScale(current === 'normal' ? 'large' : 'xlarge', true);
            });
        });
        document.querySelectorAll('[data-font-decrease]').forEach((button) => {
            button.addEventListener('click', () => {
                const current = root.dataset.fontScale || 'normal';
                applyFontScale(current === 'xlarge' ? 'large' : 'normal', true);
            });
        });

        updateThemeControls(root.dataset.theme || initialTheme);
        updateFontControls(root.dataset.fontScale || 'normal');
    });
})();