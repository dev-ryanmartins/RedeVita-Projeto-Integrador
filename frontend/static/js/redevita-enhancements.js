/* Melhorias complementares: filtros locais, feedback de formulários e sugestões. */
(function () {
    'use strict';

    function normalizar(valor) {
        return String(valor || '')
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '')
            .toLowerCase()
            .trim();
    }

    function configurarFiltro(input) {
        const table = document.getElementById(input.dataset.tableSearch);
        if (!table || !table.tBodies.length) return;

        const rows = Array.from(table.tBodies[0].rows);
        const hint = input.closest('.table-toolbar')?.querySelector('.table-search-hint');
        const textoOriginal = hint?.textContent || '';

        function aplicarFiltro() {
            const termo = normalizar(input.value);
            let visiveis = 0;
            rows.forEach((row) => {
                const vazio = row.querySelector('.empty-state');
                const corresponde = !termo || vazio || normalizar(row.textContent).includes(termo);
                row.hidden = !corresponde;
                if (corresponde && !vazio) visiveis += 1;
            });

            if (hint) {
                hint.textContent = termo
                    ? `${visiveis} item(ns) encontrado(s) nesta página.`
                    : textoOriginal;
            }
        }

        input.addEventListener('input', aplicarFiltro);
        aplicarFiltro();
    }

    function configurarFeedbackModal(form) {
        form.addEventListener('submit', function () {
            const submit = form.querySelector('button[type="submit"]');
            if (!submit || submit.dataset.feedbackApplied) return;
            submit.dataset.feedbackApplied = 'true';
            submit.dataset.originalLabel = submit.innerHTML;
            submit.disabled = true;
            submit.setAttribute('aria-busy', 'true');
            submit.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Salvando...';
        });
    }

    function configurarModais() {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.attributeName !== 'class') return;
                const overlay = mutation.target;
                const aberto = overlay.classList.contains('active');
                overlay.setAttribute('aria-hidden', aberto ? 'false' : 'true');
            });
        });
        document.querySelectorAll('.modal-overlay').forEach((overlay) => {
            overlay.setAttribute('aria-hidden', overlay.classList.contains('active') ? 'false' : 'true');
            observer.observe(overlay, { attributes: true });
            const form = overlay.querySelector('form');
            if (form) configurarFeedbackModal(form);
        });
    }

    function configurarSugestoes() {
        const input = document.querySelector('[data-fast-search-url]');
        const list = document.getElementById('busca-sugestoes');
        if (!input || !list) return;
        let timer;
        input.addEventListener('input', () => {
            clearTimeout(timer);
            const query = input.value.trim();
            if (query.length < 2) {
                list.replaceChildren();
                return;
            }
            timer = setTimeout(() => {
                fetch(`${input.dataset.fastSearchUrl}?q=${encodeURIComponent(query)}`, {
                    headers: { Accept: 'application/json' },
                })
                    .then((response) => response.ok ? response.json() : null)
                    .then((payload) => {
                        if (!payload) return;
                        const sugestoes = payload.data || payload.dados || [];
                        list.replaceChildren(...sugestoes.map((item) => {
                            const option = document.createElement('option');
                            option.value = item.label;
                            option.label = `${item.tipo === 'paciente' ? 'Paciente' : 'Medicamento'} — ${item.detalhe}`;
                            return option;
                        }));
                    })
                    .catch(() => list.replaceChildren());
            }, 180);
        });
    }

    document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('[data-table-search]').forEach(configurarFiltro);
        configurarModais();
        configurarSugestoes();
    });
})();