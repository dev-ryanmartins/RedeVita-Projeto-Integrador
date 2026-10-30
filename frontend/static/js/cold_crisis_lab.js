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

    // ==================== Replay Extension ====================

    // Elementos do DOM de Replay
    const labTabs = document.querySelectorAll('.lab-tab');
    const labTabContents = document.querySelectorAll('.lab-tab-content');
    const replayScenarioSelect = document.getElementById('replayScenarioSelect');
    const replayDuracaoHoras = document.getElementById('replayDuracaoHoras');
    const replayIntervaloMinutos = document.getElementById('replayIntervaloMinutos');
    const replaySeedInput = document.getElementById('replaySeedInput');
    const btnIniciarReplay = document.getElementById('btnIniciarReplay');
    const btnPausarReplay = document.getElementById('btnPausarReplay');
    const btnAvancarEtapa = document.getElementById('btnAvancarEtapa');
    const btnReiniciarReplay = document.getElementById('btnReiniciarReplay');
    const replayRoteiroInfo = document.getElementById('replayRoteiroInfo');
    const replayEtapasSection = document.getElementById('replayEtapasSection');
    const replayEtapasList = document.getElementById('replayEtapasList');
    const replayComparacaoSection = document.getElementById('replayComparacaoSection');
    const replayComparacaoResultados = document.getElementById('replayComparacaoResultados');
    const btnComparar = document.getElementById('btnComparar');
    const replayEmpty = document.getElementById('replayEmpty');

    // Estado do replay
    let execucaoAtual = null;
    let execucao1 = null;
    let execucao2 = null;
    let replayPausado = false;
    let tempoVirtual = 0;

    // Carregar cenários para replay
    async function carregarCenariosReplay() {
        try {
            const response = await fetch('/api/laboratorio-crise-cadeia-frio/cenarios', {
                headers: { Accept: 'application/json' }
            });

            if (!response.ok) {
                throw new Error('Erro ao carregar cenários');
            }

            const data = await response.json();
            const cenarios = data.dados?.cenarios || [];

            replayScenarioSelect.innerHTML = '<option value="">Selecione um cenário...</option>';
            cenarios.forEach(c => {
                const option = document.createElement('option');
                option.value = c.id;
                option.textContent = c.nome;
                replayScenarioSelect.appendChild(option);
            });

            atualizarBotaoIniciarReplay();
        } catch (error) {
            console.error('Erro ao carregar cenários de replay:', error);
        }
    }

    // Atualizar botão de iniciar replay
    function atualizarBotaoIniciarReplay() {
        btnIniciarReplay.disabled = !replayScenarioSelect.value;
    }

    // Iniciar replay
    async function iniciarReplay() {
        const cenario = replayScenarioSelect.value;
        const duracao = parseInt(replayDuracaoHoras.value) || 6;
        const intervalo = parseInt(replayIntervaloMinutos.value) || 15;
        const seed = replaySeedInput.value ? parseInt(replaySeedInput.value) : null;

        try {
            const response = await fetch('/api/laboratorio-crise-cadeia-frio/replay/iniciar', {
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
                throw new Error(errorData.erro?.mensagem || 'Erro ao iniciar replay');
            }

            const data = await response.json();
            execucaoAtual = data.dados || null;

            if (execucaoAtual) {
                mostrarRoteiro(cenario);
                mostrarEtapas(cenario);
                atualizarControlesReplay();
                replayEmpty.hidden = true;
            }
        } catch (error) {
            console.error('Erro ao iniciar replay:', error);
            alert(error.message || 'Erro ao iniciar replay');
        }
    }

    // Mostrar roteiro
    async function mostrarRoteiro(cenario) {
        try {
            const response = await fetch(`/api/laboratorio-crise-cadeia-frio/replay/roteiro?scenario=${scenario}`, {
                headers: { Accept: 'application/json' }
            });

            if (!response.ok) {
                throw new Error('Erro ao carregar roteiro');
            }

            const data = await response.json();
            const roteiro = data.dados?.roteiro || [];
            const informacao = data.dados?.informacao || {};

            document.getElementById('roteiroVersao').textContent = informacao.versao || '-';
            document.getElementById('roteiroData').textContent = informacao.data || '-';
            document.getElementById('roteiroAviso').textContent = informacao.aviso || '';

            replayRoteiroInfo.hidden = false;
        } catch (error) {
            console.error('Erro ao carregar roteiro:', error);
        }
    }

    // Mostrar etapas
    function mostrarEtapas(cenario) {
        const service = new ColdCrisisReplayService();
        const etapas = service.obter_roteiro(cenario);

        replayEtapasList.innerHTML = '';
        etapas.forEach(etapa => {
            const div = document.createElement('div');
            div.className = 'lab-etapa-item pendente';
            div.dataset.etapaId = etapa.id;
            div.innerHTML = `
                <input type="checkbox" id="etapa_${etapa.id}" value="${etapa.id}">
                <div class="lab-etapa-content">
                    <strong>${etapa.nome}</strong>
                    <p>${etapa.descricao}</p>
                </div>
            `;
            div.querySelector('input').addEventListener('change', function() {
                adicionarEscolhaReplay(etapa.id);
            });
            replayEtapasList.appendChild(div);
        });

        replayEtapasSection.hidden = false;
    }

    // Adicionar escolha de replay
    async function adicionarEscolhaReplay(etapaId) {
        if (!execucaoAtual) return;

        tempoVirtual += 1; // Simula tempo virtual

        try {
            const response = await fetch('/api/laboratorio-crise-cadeia-frio/replay/escolha', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({
                    execucao: execucaoAtual,
                    etapa_id: etapaId,
                    tempo_virtual: tempoVirtual
                })
            });

            if (!response.ok) {
                throw new Error('Erro ao adicionar escolha');
            }

            const data = await response.json();
            execucaoAtual = data.dados || null;

            // Atualizar UI
            const etapaItem = document.querySelector(`[data-etapa-id="${etapaId}"]`);
            if (etapaItem) {
                etapaItem.classList.remove('pendente');
                etapaItem.classList.add('coberta');
            }

            atualizarControlesReplay();
        } catch (error) {
            console.error('Erro ao adicionar escolha:', error);
        }
    }

    // Atualizar controles de replay
    function atualizarControlesReplay() {
        if (!execucaoAtual) return;

        btnPausarReplay.disabled = !execucaoAtual.escolhas.length || execucaoAtual.concluido;
        btnAvancarEtapa.disabled = execucaoAtual.concluido;
        btnReiniciarReplay.disabled = !execucaoAtual.escolhas.length;

        // Mostrar seção de comparação se houver execuções
        if (execucao1 && execucao2) {
            replayComparacaoSection.hidden = false;
        }
    }

    // Comparar execuções
    async function compararExecucoes() {
        if (!execucao1 || !execucao2) {
            alert('Execute duas vezes o mesmo cenário para comparar');
            return;
        }

        try {
            const response = await fetch('/api/laboratorio-crise-cadeia-frio/replay/comparar', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({
                    execucao1: execucao1,
                    execucao2: execucao2
                })
            });

            if (!response.ok) {
                throw new Error('Erro ao comparar execuções');
            }

            const data = await response.json();
            const comparacao = data.dados || {};

            mostrarComparacao(comparacao);
        } catch (error) {
            console.error('Erro ao comparar execuções:', error);
            alert(error.message || 'Erro ao comparar execuções');
        }
    }

    // Mostrar comparação
    function mostrarComparacao(comparacao) {
        document.getElementById('comparacaoCobertura1').textContent = comparacao.cobertura1.porcentagem_cobertura + '%';
        document.getElementById('comparacaoCobertura2').textContent = comparacao.cobertura2.porcentagem_cobertura + '%';
        document.getElementById('comparacaoTempo1').textContent = comparacao.tempo_virtual_1 + 'h';
        document.getElementById('comparacaoTempo2').textContent = comparacao.tempo_virtual_2 + 'h';

        document.getElementById('comparacaoEtapasComuns').innerHTML = comparacao.etapas_comuns.map(e => `<li>${e}</li>`).join('');
        document.getElementById('comparacaoEtapasExclusivas1').innerHTML = comparacao.etapas_exclusivas_1.map(e => `<li>${e}</li>`).join('');
        document.getElementById('comparacaoEtapasExclusivas2').innerHTML = comparacao.etapas_exclusivas_2.map(e => `<li>${e}</li>`).join('');

        replayComparacaoResultados.hidden = false;
    }

    // Reiniciar replay
    function reiniciarReplay() {
        if (execucaoAtual) {
            // Salvar execução atual para comparação
            if (!execucao1) {
                execucao1 = execucaoAtual;
            } else if (!execucao2) {
                execucao2 = execucaoAtual;
            } else {
                // Substituir a execução mais antiga
                execucao1 = execucao2;
                execucao2 = execucaoAtual;
            }
        }

        execucaoAtual = null;
        tempoVirtual = 0;
        replayPausado = false;

        // Limpar UI
        replayEtapasList.innerHTML = '';
        replayRoteiroInfo.hidden = true;
        replayEtapasSection.hidden = true;
        replayComparacaoResultados.hidden = true;
        replayEmpty.hidden = false;

        atualizarControlesReplay();
    }

    // Tabs
    labTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const tabName = this.dataset.tab;
            
            labTabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            
            labTabContents.forEach(content => content.classList.remove('active'));
            document.getElementById(`tab-${tabName}`).classList.add('active');
        });
    });

    // Event listeners de replay
    replayScenarioSelect.addEventListener('change', atualizarBotaoIniciarReplay);
    btnIniciarReplay.addEventListener('click', iniciarReplay);
    btnPausarReplay.addEventListener('click', () => { replayPausado = !replayPausado; });
    btnAvancarEtapa.addEventListener('click', () => { /* Implementar avanço automático */ });
    btnReiniciarReplay.addEventListener('click', reiniciarReplay);
    btnComparar.addEventListener('click', compararExecucoes);

    // Inicialização de replay
    carregarCenariosReplay();
})();
