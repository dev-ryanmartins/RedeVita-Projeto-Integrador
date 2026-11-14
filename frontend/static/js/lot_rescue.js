/**
 * JavaScript para Janela de Resgate de Lotes
 * Funcionalidades: busca de lotes, simulação de cenários, manipulação de etapas
 */

document.addEventListener('DOMContentLoaded', function() {
    const btnBuscar = document.getElementById('btn-buscar');
    const btnRetry = document.getElementById('btn-retry');
    const horizonDias = document.getElementById('horizon-dias');
    const filtroNome = document.getElementById('filtro-nome');
    const loadingState = document.getElementById('loading-state');
    const errorState = document.getElementById('error-state');
    const emptyState = document.getElementById('empty-state');
    const mainContent = document.getElementById('main-content');
    const errorMessage = document.getElementById('error-message');

    const modal = document.getElementById('simulation-modal');
    const closeModal = document.getElementById('close-modal');
    const btnAddEtapa = document.getElementById('btn-add-etapa');
    const btnSimular = document.getElementById('btn-simular');
    const etapasContainer = document.getElementById('etapas-container');
    const simulationResult = document.getElementById('simulation-result');
    const resultContent = document.getElementById('result-content');

    let currentLoteId = null;

    // Buscar lotes
    btnBuscar.addEventListener('click', buscarLotes);
    btnRetry.addEventListener('click', buscarLotes);

    // Enter no filtro de nome
    filtroNome.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            buscarLotes();
        }
    });

    async function buscarLotes() {
        const horizon = parseInt(horizonDias.value) || 30;
        const nome = filtroNome.value.trim();

        // Validar horizonte
        if (horizon < 1 || horizon > 365) {
            showError('Horizonte deve ser entre 1 e 365 dias');
            return;
        }

        showLoading();

        try {
            // Buscar resumo
            const resumoResponse = await fetch(`/api/janela-resgate-lotes/resumo?horizon_dias=${horizon}&nome_medicamento=${encodeURIComponent(nome)}`);
            const resumoData = await resumoResponse.json();

            if (!resumoData.sucesso) {
                throw new Error(resumoData.mensagem || 'Erro ao buscar resumo');
            }

            // Buscar lotes
            const lotesResponse = await fetch(`/api/janela-resgate-lotes/lotes?horizon_dias=${horizon}&nome_medicamento=${encodeURIComponent(nome)}`);
            const lotesData = await lotesResponse.json();

            if (!lotesData.sucesso) {
                throw new Error(lotesData.mensagem || 'Erro ao buscar lotes');
            }

            const lotes = lotesData.dados.lotes;

            if (lotes.length === 0) {
                showEmpty();
                return;
            }

            showContent();
            updateSummary(resumoData.dados);
            renderLotesTable(lotes);

        } catch (error) {
            console.error('Erro ao buscar lotes:', error);
            showError(error.message || 'Erro ao carregar dados');
        }
    }

    function showLoading() {
        loadingState.classList.remove('hidden');
        errorState.classList.add('hidden');
        emptyState.classList.add('hidden');
        mainContent.classList.add('hidden');
    }

    function showError(message) {
        loadingState.classList.add('hidden');
        errorState.classList.remove('hidden');
        emptyState.classList.add('hidden');
        mainContent.classList.add('hidden');
        errorMessage.textContent = message;
    }

    function showEmpty() {
        loadingState.classList.add('hidden');
        errorState.classList.add('hidden');
        emptyState.classList.remove('hidden');
        mainContent.classList.add('hidden');
    }

    function showContent() {
        loadingState.classList.add('hidden');
        errorState.classList.add('hidden');
        emptyState.classList.add('hidden');
        mainContent.classList.remove('hidden');
    }

    function updateSummary(resumo) {
        document.getElementById('summary-total').textContent = resumo.total_lotes;
        document.getElementById('summary-critical').textContent = resumo.lotes_criticos;
        document.getElementById('summary-attention').textContent = resumo.lotes_atencao;
        document.getElementById('summary-normal').textContent = resumo.lotes_normais;
    }

    function renderLotesTable(lotes) {
        const tbody = document.getElementById('lotes-tbody');
        tbody.innerHTML = '';

        lotes.forEach(lote => {
            const tr = document.createElement('tr');

            const statusClass = lote.status_semaforo === 2 ? 'red' : (lote.status_semaforo === 1 ? 'yellow' : 'green');
            const statusText = lote.status_semaforo === 2 ? 'Vencido' : (lote.status_semaforo === 1 ? 'Atenção' : 'Normal');

            tr.innerHTML = `
                <td>${escapeHtml(lote.nome)}</td>
                <td>${escapeHtml(lote.lote)}</td>
                <td>${formatDate(lote.data_validade)}</td>
                <td>${lote.dias_para_vencer} dias</td>
                <td>${lote.quantidade_cadastrada}</td>
                <td><span class="status-badge ${statusClass}">${statusText}</span></td>
                <td>
                    <button class="btn-simular" data-lote-id="${lote.id}" data-medicamento="${escapeHtml(lote.nome)}" data-lote="${escapeHtml(lote.lote)}" data-validade="${lote.data_validade}" data-dias="${lote.dias_para_vencer}">
                        Simular
                    </button>
                </td>
            `;

            tbody.appendChild(tr);
        });

        // Adicionar event listeners aos botões de simular
        document.querySelectorAll('.btn-simular').forEach(btn => {
            btn.addEventListener('click', function() {
                currentLoteId = parseInt(this.dataset.loteId);
                openModal(
                    this.dataset.medicamento,
                    this.dataset.lote,
                    this.dataset.validade,
                    this.dataset.dias
                );
            });
        });
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('pt-BR');
    }

    // Modal
    function openModal(medicamento, lote, validade, dias) {
        document.getElementById('sim-medicamento').textContent = medicamento;
        document.getElementById('sim-lote').textContent = lote;
        document.getElementById('sim-validade').textContent = formatDate(validade);
        document.getElementById('sim-dias').textContent = dias + ' dias';

        // Resetar etapas
        etapasContainer.innerHTML = `
            <div class="etapa-row">
                <input type="text" class="etapa-nome" placeholder="Nome da etapa (ex: Triagem)" aria-label="Nome da etapa">
                <input type="number" class="etapa-duracao" min="1" max="90" placeholder="Dias" aria-label="Duração em dias">
                <button class="btn-remove-etapa" aria-label="Remover etapa">-</button>
            </div>
        `;

        // Resetar resultado
        simulationResult.classList.add('hidden');
        resultContent.innerHTML = '';
        simulationResult.classList.remove('result-compativel', 'result-margem-reduzida', 'result-incompativel');

        // Adicionar event listeners
        document.querySelectorAll('.btn-remove-etapa').forEach(btn => {
            btn.addEventListener('click', removeEtapa);
        });

        modal.classList.remove('hidden');
    }

    closeModal.addEventListener('click', function() {
        modal.classList.add('hidden');
    });

    // Fechar modal ao clicar fora
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.classList.add('hidden');
        }
    });

    // Adicionar etapa
    btnAddEtapa.addEventListener('click', function() {
        const etapas = etapasContainer.querySelectorAll('.etapa-row');
        if (etapas.length >= 5) {
            alert('Máximo de 5 etapas permitidas');
            return;
        }

        const novaEtapa = document.createElement('div');
        novaEtapa.className = 'etapa-row';
        novaEtapa.innerHTML = `
            <input type="text" class="etapa-nome" placeholder="Nome da etapa (ex: Triagem)" aria-label="Nome da etapa">
            <input type="number" class="etapa-duracao" min="1" max="90" placeholder="Dias" aria-label="Duração em dias">
            <button class="btn-remove-etapa" aria-label="Remover etapa">-</button>
        `;

        etapasContainer.appendChild(novaEtapa);

        novaEtapa.querySelector('.btn-remove-etapa').addEventListener('click', removeEtapa);
    });

    function removeEtapa() {
        const etapas = etapasContainer.querySelectorAll('.etapa-row');
        if (etapas.length <= 1) {
            alert('Pelo menos uma etapa deve ser informada');
            return;
        }
        this.closest('.etapa-row').remove();
    }

    // Simular
    btnSimular.addEventListener('click', async function() {
        const etapas = [];
        const etapaRows = etapasContainer.querySelectorAll('.etapa-row');

        let valid = true;

        etapaRows.forEach(row => {
            const nome = row.querySelector('.etapa-nome').value.trim();
            const duracao = parseInt(row.querySelector('.etapa-duracao').value);

            if (!nome || !duracao || duracao < 1 || duracao > 90) {
                valid = false;
                return;
            }

            etapas.push({
                nome: nome,
                duracao_dias: duracao
            });
        });

        if (!valid) {
            alert('Preencha todas as etapas com nome e duração válida (1-90 dias)');
            return;
        }

        if (etapas.length === 0) {
            alert('Pelo menos uma etapa deve ser informada');
            return;
        }

        try {
            const response = await fetch('/api/janela-resgate-lotes/simular', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    lote_id: currentLoteId,
                    etapas: etapas
                })
            });

            const data = await response.json();

            if (!data.sucesso) {
                throw new Error(data.mensagem || 'Erro ao simular');
            }

            showSimulationResult(data.dados);

        } catch (error) {
            console.error('Erro ao simular:', error);
            alert(error.message || 'Erro ao simular cenário');
        }
    });

    function showSimulationResult(resultado) {
        simulationResult.classList.remove('hidden');

        // Definir classe baseada no resultado
        simulationResult.classList.remove('result-compativel', 'result-margem-reduzida', 'result-incompativel');
        if (resultado.resultado === 'compativel') {
            simulationResult.classList.add('result-compativel');
        } else if (resultado.resultado === 'margem_reduzida') {
            simulationResult.classList.add('result-margem-reduzida');
        } else {
            simulationResult.classList.add('result-incompativel');
        }

        let html = `
            <p><strong>Resultado:</strong> ${resultado.mensagem}</p>
            <p><strong>Dias até vencimento:</strong> ${resultado.dias_para_vencer} dias</p>
            <p><strong>Duração total das etapas:</strong> ${resultado.total_duracao_dias} dias</p>
            <p><strong>Margem:</strong> ${resultado.margem_dias} dias</p>
            <h4>Etapas:</h4>
            <ul>
        `;

        resultado.etapas.forEach(etapa => {
            html += `<li>${escapeHtml(etapa.nome)}: ${etapa.duracao_dias} dias</li>`;
        });

        html += `</ul>
            <h4>Limitações:</h4>
            <ul>
        `;

        resultado.limitacoes.forEach(lim => {
            html += `<li>${escapeHtml(lim)}</li>`;
        });

        html += '</ul>';

        resultContent.innerHTML = html;
    }

    // Escape para fechar modal
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
            modal.classList.add('hidden');
        }
    });
});
