/**
 * JavaScript para Radar de Integridade da Telemetria
 * Layout refeito com classes radar-*
 */

document.addEventListener('DOMContentLoaded', function() {
    const btnAnalisar = document.getElementById('btn-analisar');
    const btnRetry = document.getElementById('btn-retry');
    const dataInicio = document.getElementById('data-inicio');
    const dataFim = document.getElementById('data-fim');
    const loadingState = document.getElementById('loading-state');
    const errorState = document.getElementById('error-state');
    const emptyState = document.getElementById('empty-state');
    const mainContent = document.getElementById('main-content');
    const errorMessage = document.getElementById('error-message');
    const tabBtns = document.querySelectorAll('.radar-tab');
    const tabContents = document.querySelectorAll('.radar-tab-content');

    const btnAnalisarLacunas = document.getElementById('btn-analisar-lacunas');
    const intervaloLacunas = document.getElementById('intervalo-lacunas');
    const btnAnalisarFuturos = document.getElementById('btn-analisar-futuros');
    const toleranciaFuturos = document.getElementById('tolerancia-futuros');

    // Buscar dados iniciais
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

    // Tabs
    tabBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const tab = this.dataset.tab;
            
            // Guardar posição do scroll antes de mudar
            const scrollPosition = window.pageYOffset || document.documentElement.scrollTop;
            
            // Atualizar botões
            tabBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            // Atualizar conteúdo
            tabContents.forEach(content => content.classList.remove('active'));
            document.getElementById(`tab-${tab}`).classList.add('active');
            
            // Restaurar posição do scroll para evitar pulo
            window.scrollTo(0, scrollPosition);
        });
    });

    // Analisar lacunas
    btnAnalisarLacunas.addEventListener('click', analisarLacunas);

    // Analisar timestamps futuros
    btnAnalisarFuturos.addEventListener('click', analisarFuturos);

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

        showLoading();

        try {
            // Buscar resumo
            const resumoResponse = await fetch(`/api/radar-integridade-telemetria/resumo?periodo_dias=${diffDias}`);
            const resumoData = await resumoResponse.json();

            if (!resumoData.sucesso) {
                throw new Error(resumoData.mensagem || 'Erro ao buscar resumo');
            }

            updateSummary(resumoData.dados);

            // Buscar frescor
            const frescorResponse = await fetch(`/api/radar-integridade-telemetria/frescor?periodo_dias=${diffDias}`);
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
            showError('Erro ao carregar dados: ' + (error.message || 'Erro desconhecido'));
        }
    }

    async function analisarLacunas() {
        const inicio = new Date(dataInicio.value);
        const fim = new Date(dataFim.value);
        const diffDias = Math.ceil((fim - inicio) / (1000 * 60 * 60 * 24));
        const intervalo = intervaloLacunas.value || '1h';

        showLoading();

        try {
            const response = await fetch(`/api/radar-integridade-telemetria/lacunas?intervalo_minutos=${intervalo}&periodo_dias=${diffDias}`);
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
        const inicio = new Date(dataInicio.value);
        const fim = new Date(dataFim.value);
        const diffDias = Math.ceil((fim - inicio) / (1000 * 60 * 60 * 24));
        const tolerancia = parseInt(toleranciaFuturos.value) || 60;

        showLoading();

        try {
            const response = await fetch(`/api/radar-integridade-telemetria/futuros?tolerancia_minutos=${tolerancia}&periodo_dias=${diffDias}`);
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

    function updateSummary(data) {
        document.getElementById('summary-dispositivos').textContent = data.dispositivos || '-';
        document.getElementById('summary-sem-dados').textContent = data.sem_dados || '-';
        document.getElementById('summary-antigos').textContent = data.dados_antigos || '-';
        document.getElementById('summary-lacunas').textContent = data.lacunas || '-';
        document.getElementById('summary-duplicidades').textContent = data.duplicidades || '-';
        document.getElementById('summary-futuros').textContent = data.timestamps_futuros || '-';
    }

    function renderFrescorTable(dispositivos) {
        const tbody = document.getElementById('frescor-tbody');
        tbody.innerHTML = '';

        dispositivos.forEach(disp => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${escapeHtml(disp.dispositivo_id)}</td>
                <td>${formatDate(disp.ultima_leitura)}</td>
                <td>${disp.dias_desde_ultima ? disp.dias_desde_ultima.toFixed(1) : '-'}</td>
                <td><span class="status-badge ${disp.status_frescor}">${formatStatus(disp.status_frescor)}</span></td>
                <td>${disp.total_leituras}</td>
            `;
            tbody.appendChild(tr);
        });
    }

    function renderLacunasTable(lacunas) {
        const tbody = document.getElementById('lacunas-tbody');
        tbody.innerHTML = '';

        lacunas.forEach(lacuna => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${escapeHtml(lacuna.dispositivo_id)}</td>
                <td>${escapeHtml(lacuna.farmacia_id || '-')}</td>
                <td>${formatDate(lacuna.data_inicio)}</td>
                <td>${formatDate(lacuna.data_fim)}</td>
                <td>${lacuna.delta_minutos}</td>
                <td>${lacuna.intervalo_esperado_min}</td>
                <td><span class="gravidade-badge ${lacuna.gravidade}">${lacuna.gravidade}</span></td>
            `;
            tbody.appendChild(tr);
        });
    }

    function renderDuplicidadesTable(duplicidades) {
        const tbody = document.getElementById('duplicidades-tbody');
        tbody.innerHTML = '';

        duplicidades.forEach(dup => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${escapeHtml(dup.dispositivo_id)}</td>
                <td>${escapeHtml(dup.farmacia_id || '-')}</td>
                <td>${formatDate(dup.timestamp)}</td>
                <td>${dup.temperatura}°C</td>
                <td>${dup.umidade}%</td>
                <td>${dup.quantidade}</td>
                <td>${dup.candidatos}</td>
            `;
            tbody.appendChild(tr);
        });
    }

    function renderFuturosTable(futuros) {
        const tbody = document.getElementById('futuros-tbody');
        tbody.innerHTML = '';

        futuros.forEach(futuro => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${escapeHtml(futuro.dispositivo_id)}</td>
                <td>${escapeHtml(futuro.farmacia_id || '-')}</td>
                <td>${formatDate(futuro.timestamp)}</td>
                <td>${futuro.delta_minutos}</td>
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
        const dia = String(date.getDate()).padStart(2, '0');
        const mes = String(date.getMonth() + 1).padStart(2, '0');
        const ano = date.getFullYear();
        const horas = String(date.getHours()).padStart(2, '0');
        const minutos = String(date.getMinutes()).padStart(2, '0');
        return `${dia}/${mes}/${ano} ${horas}:${minutos}`;
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

    // Scroll-to-Top Button
    const scrollToTopBtn = document.getElementById('scroll-to-top');
    
    if (scrollToTopBtn) {
        window.addEventListener('scroll', function() {
            if (window.pageYOffset > 300) {
                scrollToTopBtn.classList.add('visible');
            } else {
                scrollToTopBtn.classList.remove('visible');
            }
        });

        scrollToTopBtn.addEventListener('click', function() {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }

    // Escape para fechar modal
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const modal = document.querySelector('.modal.active');
            if (modal) {
                modal.classList.remove('active');
            }
        }
    });
});
