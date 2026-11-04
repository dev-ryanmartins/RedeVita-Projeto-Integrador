/**
 * JavaScript para Radar de Integridade e Telemetria
 * Design Profissional e Limpo
 */

document.addEventListener('DOMContentLoaded', function() {
    const btnAnalisar = document.getElementById('btn-analisar');
    const btnRetry = document.getElementById('btn-retry');
    const intervaloAnalise = document.getElementById('intervalo-analise');
    const toleranciaAnalise = document.getElementById('tolerancia-analise');
    const dataInicio = document.getElementById('data-inicio');
    const dataFim = document.getElementById('data-fim');
    const loadingState = document.getElementById('loading-state');
    const errorState = document.getElementById('error-state');
    const emptyState = document.getElementById('empty-state');
    const mainContent = document.getElementById('main-content');
    const errorMessage = document.getElementById('error-message');
    const dataTbody = document.getElementById('data-tbody');

    // Buscar dados
    btnAnalisar.addEventListener('click', buscarDados);
    btnRetry.addEventListener('click', buscarDados);

    // Inicializar datas com período padrão de 7 dias
    function inicializarDatas() {
        const hoje = new Date();
        const seteDiasAtras = new Date(hoje);
        seteDiasAtras.setDate(hoje.getDate() - 7);

        const formatarDataISO = (data) => {
            const ano = data.getFullYear();
            const mes = String(data.getMonth() + 1).padStart(2, '0');
            const dia = String(data.getDate()).padStart(2, '0');
            return `${ano}-${mes}-${dia}`;
        };

        dataFim.value = formatarDataISO(hoje);
        dataInicio.value = formatarDataISO(seteDiasAtras);
    }

    inicializarDatas();

    async function buscarDados() {
        // Calcular período a partir das datas
        const inicio = new Date(dataInicio.value);
        const fim = new Date(dataFim.value);

        // Validar datas
        if (!dataInicio.value || !dataFim.value) {
            showError('Selecione as datas de início e fim');
            return;
        }

        if (inicio > fim) {
            showError('Data de início deve ser anterior à data de fim');
            return;
        }

        const diffDias = Math.ceil((fim - inicio) / (1000 * 60 * 60 * 24));

        if (diffDias < 1 || diffDias > 90) {
            showError('Período deve ser entre 1 e 90 dias');
            return;
        }

        const intervalo = intervaloAnalise.value || '1h';
        const tolerancia = parseInt(toleranciaAnalise.value) || 60;

        showLoading();

        try {
            // Buscar resumo geral
            const resumoResponse = await fetch(`/api/radar-integridade-telemetria/resumo?periodo_dias=${diffDias}`);
            const resumoData = await resumoResponse.json();

            if (!resumoData.sucesso) {
                throw new Error(resumoData.mensagem || 'Erro ao buscar resumo');
            }

            updateMetrics(resumoData.dados);

            // Buscar dados detalhados
            const [lacunasData, duplicidadesData, futurosData] = await Promise.all([
                fetch(`/api/radar-integridade-telemetria/lacunas?intervalo_minutos=${intervalo}&periodo_dias=${diffDias}`).then(r => r.json()),
                fetch(`/api/radar-integridade-telemetria/duplicidades?periodo_dias=${diffDias}`).then(r => r.json()),
                fetch(`/api/radar-integridade-telemetria/futuros?tolerancia_minutos=${tolerancia}&periodo_dias=${diffDias}`).then(r => r.json())
            ]);

            // Combinar todos os dados em uma tabela
            const todosDados = [];
            
            if (lacunasData.sucesso && lacunasData.dados.lacunas) {
                lacunasData.dados.lacunas.forEach(item => {
                    todosDados.push({
                        dispositivo: item.dispositivo_id,
                        farmacia: item.farmacia_id || '-',
                        timestamp: item.data_inicio,
                        temperatura: '-',
                        umidade: '-',
                        status: 'Lacuna',
                        gravidade: item.gravidade
                    });
                });
            }

            if (duplicidadesData.sucesso && duplicidadesData.dados.duplicidades) {
                duplicidadesData.dados.duplicidades.forEach(item => {
                    todosDados.push({
                        dispositivo: item.dispositivo_id,
                        farmacia: item.farmacia_id || '-',
                        timestamp: item.timestamp,
                        temperatura: item.temperatura,
                        umidade: item.umidade,
                        status: 'Duplicidade',
                        gravidade: '-'
                    });
                });
            }

            if (futurosData.sucesso && futurosData.dados.futuros) {
                futurosData.dados.futuros.forEach(item => {
                    todosDados.push({
                        dispositivo: item.dispositivo_id,
                        farmacia: item.farmacia_id || '-',
                        timestamp: item.timestamp,
                        temperatura: item.temperatura,
                        umidade: item.umidade,
                        status: 'Timestamp Futuro',
                        gravidade: item.delta_minutos > item.tolerancia_minutos ? 'Alta' : 'Moderada'
                    });
                });
            }

            if (todosDados.length === 0) {
                showEmpty();
                return;
            }

            showContent();
            renderDataTable(todosDados);

        } catch (error) {
            console.error('Erro ao buscar dados:', error);
            showError('Erro ao carregar dados: ' + (error.message || 'Erro desconhecido'));
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

    function updateMetrics(data) {
        document.getElementById('metric-lacunas').textContent = data.lacunas || 0;
        document.getElementById('metric-duplicidades').textContent = data.duplicidades || 0;
        document.getElementById('metric-futuros').textContent = data.timestamps_futuros || 0;
        document.getElementById('metric-dispositivos').textContent = data.dispositivos || 0;
    }

    function renderDataTable(dados) {
        dataTbody.innerHTML = '';

        dados.forEach(item => {
            const tr = document.createElement('tr');
            
            let statusClass = 'radar-status-neutral';
            if (item.status === 'Lacuna') {
                statusClass = item.gravidade === 'Alta' ? 'radar-status-danger' : 'radar-status-warning';
            } else if (item.status === 'Duplicidade') {
                statusClass = 'radar-status-warning';
            } else if (item.status === 'Timestamp Futuro') {
                statusClass = item.gravidade === 'Alta' ? 'radar-status-danger' : 'radar-status-warning';
            }

            tr.innerHTML = `
                <td>${escapeHtml(item.dispositivo)}</td>
                <td>${escapeHtml(item.farmacia)}</td>
                <td>${formatDate(item.timestamp)}</td>
                <td>${item.temperatura !== '-' ? item.temperatura + '°C' : '-'}</td>
                <td>${item.umidade !== '-' ? item.umidade + '%' : '-'}</td>
                <td><span class="${statusClass}">${item.status}</span></td>
            `;
            dataTbody.appendChild(tr);
        });
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function formatDate(dateString) {
        const date = new Date(dateString);
        const dia = String(date.getDate()).padStart(2, '0');
        const mes = String(date.getMonth() + 1).padStart(2, '0');
        const ano = date.getFullYear();
        const horas = String(date.getHours()).padStart(2, '0');
        const minutos = String(date.getMinutes()).padStart(2, '0');
        return `${dia}/${mes}/${ano} ${horas}:${minutos}`;
    }

    // Escape para fechar modais
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const modal = document.querySelector('.modal.active');
            if (modal) {
                modal.classList.remove('active');
            }
        }
    });
});
