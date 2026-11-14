(function () {
    'use strict';

    const root = document.querySelector('[data-perfil-resiliencia]');
    if (!root) return;

    const prListContent = document.getElementById('prListContent');
    const prLoading = document.getElementById('prLoading');

    async function carregarPerfis() {
        try {
            const response = await fetch('/api/perfil-resiliencia/todos', {
                headers: { Accept: 'application/json' }
            });

            if (!response.ok) {
                throw new Error('Erro ao carregar perfis');
            }

            const data = await response.json();
            const perfis = data.dados?.perfis || [];

            if (perfis.length === 0) {
                prListContent.innerHTML = '<p class="pr-empty">Nenhum perfil cadastrado.</p>';
                return;
            }

            // Renderizar lista
            let html = '<div class="pr-cards-grid">';
            perfis.forEach(perfil => {
                html += `
                    <div class="pr-card">
                        <h4>${perfil.farmacia_nome}</h4>
                        <div class="pr-status ${perfil.desatualizado ? 'desatualizado' : 'atualizado'}">
                            ${perfil.desatualizado ? 'Desatualizado' : 'Atualizado'}
                        </div>
                        <div class="pr-details">
                            <p><strong>Energia:</strong> ${perfil.situacao_energia}</p>
                            <p><strong>Refrigeração:</strong> ${perfil.situacao_refrigeracao}</p>
                            <p><strong>Apoio:</strong> ${perfil.apoio_temporario}</p>
                            <p><strong>Plano:</strong> ${perfil.plano_contingencia}</p>
                        </div>
                    </div>
                `;
            });
            html += '</div>';
            prListContent.innerHTML = html;

        } catch (error) {
            console.error('Erro ao carregar perfis:', error);
            prListContent.innerHTML = '<p class="pr-error">Erro ao carregar perfis.</p>';
        }
    }

    carregarPerfis();
})();
