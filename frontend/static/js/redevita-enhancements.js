/* ==========================================================================
   REDEVITA ENHANCEMENTS:
   - Sistema de Notificações Flutuantes (Toasts)
   - Substituição do window.alert por Toasts modernos
   - Busca Instantânea em Tabelas (Sem recarregar a página)
   - Feedback de Formulários e Modais
   ========================================================================== */
(function () {
    'use strict';

    function normalizar(valor) {
        return String(valor || '')
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '')
            .toLowerCase()
            .trim();
    }

    function escapeHTML(str) {
        return String(str || '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    // ==========================================================================
    // 1. SISTEMA DE NOTIFICAÇÕES FLUTUANTES (TOASTS)
    // ==========================================================================
    function obterOuCriarToastContainer() {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.setAttribute('aria-live', 'polite');
            container.setAttribute('aria-atomic', 'true');
            document.body.appendChild(container);
        }
        return container;
    }

    function showToast(message, type, duration, customTitle) {
        if (!message) return;
        type = type || 'success';
        if (type === 'danger') type = 'error';
        duration = typeof duration === 'number' ? duration : 4200;

        const container = obterOuCriarToastContainer();
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.setAttribute('role', 'status');

        let iconClass = 'ph-check-circle';
        let defaultTitle = 'Sucesso';
        if (type === 'error') {
            iconClass = 'ph-warning-circle';
            defaultTitle = 'Atenção';
        } else if (type === 'warning') {
            iconClass = 'ph-warning';
            defaultTitle = 'Aviso';
        } else if (type === 'info') {
            iconClass = 'ph-info';
            defaultTitle = 'Informação';
        }

        const titleText = customTitle || defaultTitle;

        toast.innerHTML = `
            <div class="toast-icon"><i class="ph-duotone ${iconClass}"></i></div>
            <div class="toast-content">
                <span class="toast-title">${escapeHTML(titleText)}</span>
                <span class="toast-message">${escapeHTML(message)}</span>
            </div>
            <button type="button" class="toast-close" aria-label="Fechar notificação">&times;</button>
            <div class="toast-progress" style="animation-duration: ${duration}ms;"></div>
        `;

        const closeBtn = toast.querySelector('.toast-close');
        let removeTimeout = null;

        function fecharToast() {
            if (removeTimeout) clearTimeout(removeTimeout);
            toast.classList.remove('show');
            toast.classList.add('hide');
            setTimeout(() => {
                if (toast.parentElement) toast.remove();
            }, 280);
        }

        closeBtn.addEventListener('click', fecharToast);

        container.appendChild(toast);

        // Disparo suave de animação após inserção no DOM
        requestAnimationFrame(() => {
            toast.classList.add('show');
        });

        removeTimeout = setTimeout(fecharToast, duration);
        return toast;
    }

    // Expor globalmente
    window.showToast = showToast;
    window.toast = {
        success: (msg, dur, tit) => showToast(msg, 'success', dur, tit),
        error: (msg, dur, tit) => showToast(msg, 'error', dur, tit),
        warning: (msg, dur, tit) => showToast(msg, 'warning', dur, tit),
        info: (msg, dur, tit) => showToast(msg, 'info', dur, tit)
    };

    // Substituir window.alert por toasts modernos e não-bloqueantes
    const originalAlert = window.alert;
    window.alert = function (msg) {
        if (!msg) return;
        showToast(String(msg), 'info', 5000);
    };

    // Capturar flash messages geradas pelo backend e exibir como Toasts
    function processarFlashMessages() {
        const flashes = document.querySelectorAll('.flash-messages .alert, .alert-banner.alert-temporary');
        flashes.forEach((el) => {
            let tipo = 'info';
            if (el.classList.contains('alert-success')) tipo = 'success';
            else if (el.classList.contains('alert-danger') || el.classList.contains('alert-error')) tipo = 'error';
            else if (el.classList.contains('alert-warning')) tipo = 'warning';

            const clone = el.cloneNode(true);
            clone.querySelectorAll('button, i, svg').forEach((n) => n.remove());
            const texto = clone.textContent.trim();
            if (texto) {
                showToast(texto, tipo, 4500);
                // Oculta gradualmente o banner estático para evitar duplicidade visual
                setTimeout(() => {
                    el.style.transition = 'opacity 0.35s ease, max-height 0.35s ease';
                    el.style.opacity = '0';
                    setTimeout(() => el.remove(), 380);
                }, 2000);
            }
        });

        // Verificar parâmetros de URL (ex: ?logout=1 ou ?msg=...)
        try {
            const params = new URLSearchParams(window.location.search);
            if (params.has('logout')) {
                showToast('Sessão encerrada com sucesso.', 'info', 4000);
                const url = new URL(window.location);
                url.searchParams.delete('logout');
                window.history.replaceState({}, document.title, url.pathname + (url.search || ''));
            } else if (params.has('pwd_reset')) {
                showToast('Senha redefinida com sucesso! Você já pode acessar sua conta.', 'success', 5000);
                const url = new URL(window.location);
                url.searchParams.delete('pwd_reset');
                window.history.replaceState({}, document.title, url.pathname + (url.search || ''));
            } else if (params.has('cadastrado')) {
                showToast('Cadastro realizado com sucesso! Faça login para continuar.', 'success', 5000);
                const url = new URL(window.location);
                url.searchParams.delete('cadastrado');
                window.history.replaceState({}, document.title, url.pathname + (url.search || ''));
            } else if (params.has('msg')) {
                const tipo = params.get('tipo') || 'success';
                showToast(params.get('msg'), tipo, 4500);
                const url = new URL(window.location);
                url.searchParams.delete('msg');
                url.searchParams.delete('tipo');
                window.history.replaceState({}, document.title, url.pathname + (url.search || ''));
            }
        } catch (e) {
            // Ignora falhas de parse de URL
        }
    }

    // ==========================================================================
    // 2. BUSCA INSTANTÂNEA EM TABELAS (SEM RECARREGAR A PÁGINA)
    // ==========================================================================
    function encontrarTabelaAlvo(input) {
        if (input.dataset.tableSearch) {
            const el = document.getElementById(input.dataset.tableSearch);
            if (el) return el;
        }
        // Tentar tabela mais próxima no wrapper ou na página
        const container = input.closest('.page-wrapper, .dashboard-container, main, body');
        if (container) {
            const tab = container.querySelector('table.styled-table, table.modern-table, table');
            if (tab) return tab;
        }
        return document.querySelector('table.styled-table, table');
    }

    function configurarFiltro(input) {
        if (input.dataset.filtroAtivo === 'true') return;
        input.dataset.filtroAtivo = 'true';

        const table = encontrarTabelaAlvo(input);
        if (!table || !table.tBodies || !table.tBodies.length) return;

        const tbody = table.tBodies[0];
        const hint = input.closest('.table-toolbar')?.querySelector('.table-search-hint') ||
                     input.parentElement?.querySelector('.table-search-hint');
        const textoOriginalHint = hint ? (hint.textContent || '') : '';

        function aplicarFiltro() {
            const termo = normalizar(input.value);
            // Ignorar a linha de empty-state temporária se já existir
            const rows = Array.from(tbody.rows).filter((r) => !r.classList.contains('table-search-empty-state'));

            let visiveis = 0;
            rows.forEach((row) => {
                // Verificar se a página tem filtro secundário (ex: tarja em inventário)
                const tarjaFiltro = window.tarjaAtual;
                const rowTarja = row.getAttribute('data-tarja') || '';
                const atendeTarja = !tarjaFiltro || rowTarja === tarjaFiltro;

                const textoLinha = normalizar(row.textContent);
                const atendeTermo = !termo || textoLinha.includes(termo);

                const atendeAmbos = atendeTermo && atendeTarja;
                row.style.display = atendeAmbos ? '' : 'none';
                if (atendeAmbos) visiveis++;
            });

            // Gerenciar linha de "Nenhum resultado"
            let emptyRow = tbody.querySelector('.table-search-empty-state');
            if (visiveis === 0 && rows.length > 0 && termo) {
                if (!emptyRow) {
                    emptyRow = document.createElement('tr');
                    emptyRow.className = 'table-search-empty-state';
                    const colCount = table.querySelectorAll('thead th').length || 6;
                    emptyRow.innerHTML = `
                        <td colspan="${colCount}" style="text-align:center; padding:32px 16px; color:var(--text-muted); font-size:0.9rem;">
                            <i class="ph-duotone ph-magnifying-glass" style="font-size:1.8rem; display:block; margin:0 auto 8px auto; opacity:0.6;"></i>
                            Nenhum resultado encontrado para <strong>"${escapeHTML(input.value)}"</strong>.
                        </td>
                    `;
                    tbody.appendChild(emptyRow);
                }
                emptyRow.style.display = '';
            } else if (emptyRow) {
                emptyRow.style.display = 'none';
            }

            // Atualizar o contador no hint
            if (hint) {
                if (termo) {
                    hint.textContent = visiveis === 1
                        ? '1 item encontrado'
                        : `${visiveis} itens encontrados`;
                } else {
                    hint.textContent = textoOriginalHint;
                }
            }
        }

        // Ouvir tanto input quanto keyup para resposta dinâmica imediata
        input.addEventListener('input', aplicarFiltro);
        input.addEventListener('keyup', aplicarFiltro);

        // Permitir limpar com tecla Esc
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                input.value = '';
                aplicarFiltro();
            }
        });

        // Se já tiver valor na inicialização
        if (input.value) {
            aplicarFiltro();
        }
    }

    function inicializarBuscasInstantaneas() {
        // Encontra todos os inputs de busca em tabelas
        const inputs = document.querySelectorAll(
            '[data-table-search], .table-search input, .table-toolbar input[type="search"], .table-toolbar input[type="text"], #inventory-table-search'
        );
        inputs.forEach(configurarFiltro);
    }

    // ==========================================================================
    // 3. FEEDBACK DE FORMULÁRIOS E MODAIS
    // ==========================================================================
    function configurarFeedbackModal(form) {
        form.addEventListener('submit', function () {
            const submit = form.querySelector('button[type="submit"]');
            if (!submit || submit.dataset.feedbackApplied) return;
            submit.dataset.feedbackApplied = 'true';
            submit.dataset.originalLabel = submit.innerHTML;
            submit.disabled = true;
            submit.setAttribute('aria-busy', 'true');
            submit.innerHTML = '<i class="ph-duotone ph-spinner ph-spin"></i> Processando...';
        });
    }

    function configurarModais() {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.attributeName !== 'class') return;
                const overlay = mutation.target;
                const aberto = overlay.classList.contains('active') || overlay.style.display === 'flex';
                overlay.setAttribute('aria-hidden', aberto ? 'false' : 'true');
            });
        });
        document.querySelectorAll('.modal-overlay').forEach((overlay) => {
            const aberto = overlay.classList.contains('active') || overlay.style.display === 'flex';
            overlay.setAttribute('aria-hidden', aberto ? 'false' : 'true');
            observer.observe(overlay, { attributes: true });
            const form = overlay.querySelector('form');
            if (form) configurarFeedbackModal(form);
        });
    }

    // ==========================================================================
    // INICIALIZAÇÃO AUTOMÁTICA
    // ==========================================================================
    function init() {
        processarFlashMessages();
        inicializarBuscasInstantaneas();
        configurarModais();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
