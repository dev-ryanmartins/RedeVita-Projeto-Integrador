/**
 * JavaScript para Radar de Integridade da Telemetria
 * Funcionalidades: análise de sinais, tabs, filtros e visualização
 */

document.addEventListener('DOMContentLoaded', function() {
    const btnAnalisar = document.getElementById('btn-analisar');
    const btnRetry = document.getElementById('btn-retry');
    const periodoDias = document.getElementById('periodo-dias');
    const loadingState = document.getElementById('loading-state');
    const errorState = document('error-state');
    const emptyState = document.getElementById('empty-state');
    const mainContent = document.getElementById('main-content');
    const errorMessage = document.getElementById('error-message');
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    const btnAnalisarLacunas = document.getElementById('btn-analisar-lacunas');
    const intervaloLacunas = document.getElementById('intervalo-lacunas');
    const btnAnalisarFuturos = document.getElementById('btn-analisar-futuros');
    const toleranciaFuturos = document.getElementById('tolerancia-futuros');

    // Buscar dados iniciais
    btnAnalisar.addEventListener('click', buscarDados);
    btnRetry.addEventListener('click', buscarDados);

    // Tabs
    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const tab = this.dataset.tab;
            
            // Atualizar botões
            tabBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            // Atualizar conteúdo
            tabContents.forEach(content => content.classList.remove('active'));
            document.getElementById(`tab-${tab}`).classList.add('active');
        });
    });

    // Analisar lacunas
    btnAnalisarLacunas.addEventListener('click', analisarLacunas);

    // Analisar timestamps futuros
    btnAnalisarFuturos.addEventListener('click', analisarFuturos);

    async function buscarDados() {
        const periodo = parseInt(periodoDias.value) || 7;

        // Validar período
        if (periodo < 1 || periodo > 90) {
            showError('Período deve ser entre 1 e 90 dias');
            return;
        }

        showLoading();

        try {
            // Buscar resumo
            const resumoResponse = await fetch(`/api/radar-integridade-telemetria/resumo?periodo_dias=${periodo}`);
            const resumoData = await resumoResponse.json();

            if (!resumoData.sucesso) {
                throw new Error(resumoData.mensagem || 'Erro ao buscar resumo');
            }

            updateSummary(resumoData.dados);

            // Buscar frescor
            const frescorResponse = await fetch(`/api/radar-integridade-telemetria/frescor?periodo_dias=${periodo}`);
            const frescorData = await frescorResponse.json();

            if (!frescorData.sucesso) {
                throw new Error(frescorData.mensagem || 'Erro ao analisar frescor');
            }

            if (frescorData.dados.total === 0) {
                showEmpty();
                return;
            }

            showContent();
            renderFrescorTable(frescorData.dados.dispositivos);

        } catch (error) {
            console.error('Erro ao buscar dados:', error);
            showError(error.message || 'Erro ao carregar dados');
        }
    }

    async function analisarLacunas() {
        const periodo = parseInt(periodoDias.value) || 7;
        const intervalo = intervaloLacunas.value || '1h';

        showLoading();

        try {
            const response = await fetch(`/api/radar-integridade-telemetria/lacunas?intervalo_minutos=${intervalo}&periodo_dias=${periodo}`);
            const data = await response.json();

            if (!data.sucesso) {
                throw new Error(data.mensagem || 'Erro ao analisar lacunas');
            }

            showContent();
            renderLacunasTable(data.dados.lacunas);

        } catch (error) {
            console.error('Erro ao analisar lacunas:', error);
            showError(error.message || 'Erro ao analisar lacunas');
        }
    }

    async function analisarFuturos() {
        const periodo = parseInt(periodoDias.value) || 7;
        const tolerancia = parseInt(toleranciaFuturos.value) || 60;

        showLoading();

        try {
            const response = await fetch(`/api/radar-integridade-telemetria/futuros?tolerancia_minutos=${tolerancia}&periodo_dias=${periodo}`);
            const data = await response.json();

            if (!data.sucesso) {
                throw new Error(data.mensagem || 'Erro ao analisar timestamps futuros');
            }

            showContent();
            renderFuturosTable(data.dados.futuros);

        } catch (error) {
            console.error('Erro ao analisar timestamps futuros:', error);
            showError(error.message || 'Erro ao analisar timestamps futuros');
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
        document.getElementById('summary-dispositivos').textContent = resumo.total_dispositivos;
        document.getElementById('summary-sem-dados').textContent = resumo.dispositivos_sem_dados;
        document.getElementById('summary-antigos').textContent = resumo.dispositivos_antigos;
        document.getElementById('summary-lacunas').textContent = resumo.total_lacunas;
        document.getElementById('summary-duplicidades').textContent = resumo.total_duplicidades;
        document.getElementById('summary-futuros').textContent = resumo.total_futuros;
    }

    function renderFrescorTable(dispositivos) {
        const tbody = document.getElementById('frescor-tbody');
        tbody.innerHTML = '';

        dispositivos.forEach(dispositivo => {
            const tr = document.createElement('tr');

            const statusClass = dispositivo.status_frescor === 'recente' ? 'recente' : 
                               dispositivo.status_frescor === 'moderado' ? 'moderado' : 
                               dispositivo.status_frescor === 'antigo' ? 'antigo' : 'sem_dados';

            const dias = dispositivo.dias_desde_ultima ? dispositivo.dias_desde_ultima.toFixed(1) : '-';
            const horas = dispositivo.horas_desde_ultima ? dispositivo.horas_desde_ultima.toFixed(1) : '-';

            tr.innerHTML = `
                <td>${escapeHtml(dispositivo.dispositivo_id)}</td>
                <td>${dispositivo.ultima_leitura ? formatDate(dispositivo.ultima_leitura) : '-'}</td>
                <td>${dias} dias (${horas}h)</td>
                <td><span class="status-badge ${statusClass}">${formatStatus(dispositivo.status_frescor)}</span></td>
                <td>${dispositivo.total_leituras}</td>
            `;

            tbody.appendChild(tr);
        });
    }

    function renderLacunasTable(lacunas) {
        const tbody = document.getElementById('lacunas-tbody');
        tbody.innerHTML = '';

        if (lacunas.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; color:#94a3b8;">Nenhuma lacuna detectada neste intervalo.</td></tr>';
            return;
        }

        lacunas.forEach(lacuna => {
            const tr = document.createElement('tr');

            const gravidadeClass = lacuna.gravidade === 'alta' ? 'alta' : 'moderada';

            tr.innerHTML = `
                <td>${escapeHtml(lacuna.dispositivo_id)}</td>
                <td>${lacuna.farmacia_id}</td>
                <td>${formatDate(lacuna.timestamp_anterior)}</td>
                <td>${formatDate(lacuna.timestamp_atual)}</td>
                <td>${lacuna.delta_minutos.toFixed(1)}</td>
                <td>${lacuna.intervalo_esperado_minutos}</td>
                <td><span class="gravidade-badge ${gravidadeClass}">${lacuna.gravidade}</span></td>
            `;

            tbody.appendChild(tr);
        });
    }

    function renderDuplicidadesTable(duplicidades) {
        const tbody = document.getElementById('duplicidades-tbody');
        tbody.innerHTML = '';

        if (duplicidades.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; color:#94a3b8;">Nenhum candidato a duplicidade detectado.</td></tr>';
            return;
        }

        duplicidades.forEach(dup => {
            const tr = document.createElement('tr');

            tr.innerHTML = `
                <td>${escapeHtml(dup.dispositivo_id)}</td>
                <td>${dup.farmacia_id}</td>
                <td>${formatDate(dup.timestamp)}</td>
                <td>${dup.temperatura}°C</td>
                <td>${dup.umidade}%</td>
                <td>${dup.quantidade}</td>
                <td><span class="status-badge antigo">Candidato a duplicidade</span></td>
            `;

            tbody.appendChild(tr);
        });
    }

    function renderFuturosTable(futuros) {
        const tbody = document.getElementById('futuros-tbody');
        tbody.innerHTML = '';

        if (futuros.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; color:#94a3b8;">Nenhum timestamp no futuro detectado.</td></tr>';
            return;
        }

        futuros.forEach(futuro => {
            const tr = document.createElement('tr');

            tr.innerHTML = `
                <td>${escapeHtml(futuro.dispositivo_id)}</td>
                <td>${futuro.farmacia_id}</td>
                <td>${formatDate(futuro.data_hora)}</td>
                <td>${futuro.delta_minutos.toFixed(1)}</td>
                <td>${futuro.tolerancia_minutos}</td>
                <td>${futuro.temperatura}°C</td>
                <td>${futuro.umidade}%</td>
            `;

            tbody.appendChild(tr);
        });
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleString('pt-BR');
    }

    function formatStatus(status) {
        const mapa = {
            'recente': 'Recente',
            'moderado': 'Moderado',
            'antigo': 'Antigo',
            'sem_dados': 'Sem dados'
        };
        return mapa[status] || status;
    }

    // Escape para fechar modal
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            // Fechar qualquer modal se existir
            const modal = document.querySelector('.modal.active');
            if (modal) {
                modal.classList.remove('active');
            }
        }
    });
});
