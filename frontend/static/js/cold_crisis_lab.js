(function () {
    'use strict';

    const root = document.querySelector('[data-cold-crisis-lab]');
    if (!root) return;

    // Elementos do DOM
    const cenarioSelect = document.getElementById('cenarioSelect');
    const duracaoHoras = document.getElementById('duracaoHoras');
    const intervaloMinutos = document.getElementById('intervaloMinutos');
    const seedInput = document.getElementById('seedInput');
    const btnSimular = document.getElementById('btnSimular');
    const btnLimpar = document.getElementById('btnLimpar');
    const labLoading = document.getElementById('labLoading');
    const labError = document.getElementById('labError');
    const labErrorMessage = document.getElementById('labErrorMessage');
    const labResults = document.getElementById('labResults');
    const labEmpty = document.getElementById('labEmpty');

    // Elementos de resultados
    const resultadoCenario = document.getElementById('resultadoCenario');
    const resultadoSeed = document.getElementById('resultadoSeed');
    const statTotalLeituras = document.getElementById('statTotalLeituras');
    const statTempMin = document.getElementById('statTempMin');
    const statTempMax = document.getElementById('statTempMax');
    const statTempMedia = document.getElementById('statTempMedia');
    const statNormal = document.getElementById('statNormal');
    const statAlerta = document.getElementById('statAlerta');
    const statCritico = document.getElementById('statCritico');
    const statFrio = document.getElementById('statFrio');
    const labEventsList = document.getElementById('labEventsList');
    const labReadingsTableBody = document.getElementById('labReadingsTableBody');

    // Carregar cenários disponíveis
    async function carregarCenarios() {
        try {
            const response = await fetch('/api/laboratorio-crise-cadeia-frio/cenarios', {
                headers: { Accept: 'application/json' }
            });

            if (!response.ok) {
                throw new Error('Erro ao carregar cenários');
            }

            const data = await response.json();
            const cenarios = data.dados?.cenarios || [];

            // Limpar opções existentes
            cenarioSelect.innerHTML = '<option value="">Selecione um cenário...</option>';

            // Adicionar cenários
            cenarios.forEach(cenario => {
                const option = document.createElement('option');
                option.value = scenario.id;
                option.textContent = `${scenario.nome} - ${scenario.descricao}`;
                cenarioSelect.appendChild(option);
            });
        } catch (error) {
            console.error('Erro ao carregar cenários:', error);
            mostrarErro('Erro ao carregar cenários disponíveis');
        }
    }

    // Habilitar/desabilitar botão de simulação
    function atualizarBotaoSimular() {
        const cenarioSelecionado = cenarioSelect.value;
        btnSimular.disabled = !cenarioSelecionado;
    }

    // Mostrar estado de carregamento
    function mostrarCarregamento() {
        labLoading.hidden = false;
        labError.hidden = true;
        labResults.hidden = true;
        labEmpty.hidden = true;
        btnSimular.disabled = true;
    }

    // Ocultar estado de carregamento
    function ocultarCarregamento() {
        labLoading.hidden = true;
        btnSimular.disabled = false;
        atualizarBotaoSimular();
    }

    // Mostrar erro
    function mostrarErro(mensagem) {
        labErrorMessage.textContent = mensagem;
        labError.hidden = false;
        ocultarCarregamento();
    }

    // Mostrar resultados
    function mostrarResultados(resultado) {
        labResults.hidden = false;
        labEmpty.hidden = true;

        // Metadados
        resultadoCenario.textContent = `Cenário: ${resultado.cenario}`;
        resultadoSeed.textContent = resultado.seed ? `Seed: ${resultado.seed}` : 'Seed: Aleatório';

        // Estatísticas
        const stats = resultado.estatisticas || {};
        statTotalLeituras.textContent = stats.total_leituras || 0;
        statTempMin.textContent = `${stats.temperatura_min || 0}°C`;
        statTempMax.textContent = `${stats.temperatura_max || 0}°C`;
        statTempMedia.textContent = `${stats.temperatura_media || 0}°C`;
        statNormal.textContent = stats.status_normal || 0;
        statAlerta.textContent = stats.status_alerta || 0;
        statCritico.textContent = stats.status_critico || 0;
        statFrio.textContent = stats.status_frio || 0;

        // Eventos
        labEventsList.innerHTML = '';
        const eventos = resultado.eventos || [];
        eventos.forEach(evento => {
            const eventItem = document.createElement('div');
            eventItem.className = 'lab-event-item';

            const timestamp = new Date(evento.timestamp).toLocaleString('pt-BR', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });

            eventItem.innerHTML = `
                <span class="event-time">${timestamp}</span>
                <div class="event-content">
                    <div class="event-type">${evento.tipo}</div>
                    <div class="event-description">${evento.descricao}</div>
                </div>
            `;
            labEventsList.appendChild(eventItem);
        });

        // Leituras
        labReadingsTableBody.innerHTML = '';
        const leituras = resultado.leituras || [];
        leituras.forEach(leitura => {
            const row = document.createElement('tr');

            const timestamp = new Date(leitura.timestamp).toLocaleString('pt-BR', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });

            row.innerHTML = `
                <td>${timestamp}</td>
                <td>${leitura.dispositivo_id}</td>
                <td>${leitura.temperatura}°C</td>
                <td>${leitura.umidade}%</td>
                <td><span class="status-badge ${leitura.status}">${leitura.status}</span></td>
            `;
            labReadingsTableBody.appendChild(row);
        });
    }

    // Limpar resultados
    function limparResultados() {
        labResults.hidden = true;
        labEmpty.hidden = false;
        labError.hidden = true;
        cenarioSelect.value = '';
        duracaoHoras.value = 6;
        intervaloMinutos.value = 15;
        seedInput.value = '';
        atualizarBotaoSimular();
    }

    // Executar simulação
    async function executarSimulacao() {
        const cenario = cenarioSelect.value;
        const duracao = parseInt(duracaoHoras.value, 10);
        const intervalo = parseInt(intervaloMinutos.value, 10);
        const seed = seedInput.value ? parseInt(seedInput.value, 10) : null;

        // Validações
        if (!cenario) {
            mostrarErro('Selecione um cenário');
            return;
        }

        if (isNaN(duracao) || duracao < 1 || duracao > 24) {
            mostrarErro('Duração deve ser entre 1 e 24 horas');
            return;
        }

        if (isNaN(intervalo) || intervalo < 1 || intervalo > 60) {
            mostrarErro('Intervalo deve ser entre 1 e 60 minutos');
            return;
        }

        mostrarCarregamento();

        try {
            const response = await fetch('/api/laboratorio-crise-cadeia-frio/simular', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({
                    cenario: cenario,
                    duracao_horas: duracao,
                    intervalo_minutos: intervalo,
                    seed: seed
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.erro?.mensagem || 'Erro ao executar simulação');
            }

            const data = await response.json();
            const resultado = data.dados || {};

            mostrarResultados(resultado);
        } catch (error) {
            console.error('Erro ao executar simulação:', error);
            mostrarErro(error.message || 'Erro ao executar simulação');
        } finally {
            ocultarCarregamento();
        }
    }

    // Event listeners
    cenarioSelect.addEventListener('change', atualizarBotaoSimular);
    btnSimular.addEventListener('click', executarSimulacao);
    btnLimpar.addEventListener('click', limparResultados);

    // Inicialização
    carregarCenarios();
    atualizarBotaoSimular();
})();
