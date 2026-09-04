(function () {
    'use strict';
    const root = document.querySelector('[data-iot-monitor]');
    if (!root) return;
    const endpoint = '/api/v1/monitoramento-iot/snapshot';
    const sensorsContainer = root.querySelector('[data-iot-sensors]');
    const statusClass = (status) => status === 'NORMAL' ? 'green' : status.includes('CRÍTICO') ? 'red' : 'yellow';

    function atualizarCard(sensor) {
        let card = sensorsContainer.querySelector(`[data-sensor-key="${CSS.escape(sensor.sensor_key)}"]`);
        if (!card) {
            card = document.createElement('article');
            card.className = 'iot-sensor-card';
            card.dataset.sensorKey = sensor.sensor_key;
            card.innerHTML = `
                <div class="iot-sensor-header"><div><h3></h3><p></p></div><span class="status-pill" data-iot-status-pill></span></div>
                <div class="iot-reading-grid">
                    <div class="iot-reading"><span>Temperatura</span><strong data-iot-temperature></strong></div>
                    <div class="iot-reading"><span>Umidade</span><strong data-iot-humidity></strong></div>
                </div>`;
            sensorsContainer.appendChild(card);
        }
        card.querySelector('h3').textContent = sensor.sensor_id;
        card.querySelector('p').textContent = sensor.localizacao;
        card.querySelector('[data-iot-status-pill]').textContent = sensor.status;
        card.querySelector('[data-iot-status-pill]').className = `status-pill ${statusClass(sensor.status)}`;
        card.querySelector('[data-iot-temperature]').textContent = `${sensor.temperatura} °C`;
        card.querySelector('[data-iot-humidity]').textContent = `${sensor.umidade}%`;
        card.classList.toggle('is-alert', sensor.status !== 'NORMAL' && !sensor.status.includes('CRÍTICO'));
        card.classList.toggle('is-critical', sensor.status.includes('CRÍTICO'));
    }

    function atualizarPainel(payload) {
        const dados = payload.data || payload.dados || {};
        (dados.sensores || []).forEach(atualizarCard);
        root.querySelector('[data-iot-total]').textContent = dados.total ?? 0;
        root.querySelector('[data-iot-alerts]').textContent = dados.alertas ?? 0;
        root.querySelector('[data-iot-alert-card]').classList.toggle('is-alert', Boolean(dados.alertas));
        root.querySelector('[data-iot-status]').textContent = dados.alertas ? 'Atenção' : 'Operacional';
        const time = root.querySelector('[data-iot-updated]');
        const date = new Date(dados.atualizado_em || Date.now());
        time.dateTime = date.toISOString();
        time.textContent = date.toLocaleString('pt-BR');
    }

    function atualizar() {
        const button = root.querySelector('[data-iot-refresh]');
        if (button) button.disabled = true;
        fetch(endpoint, { headers: { Accept: 'application/json' } })
            .then((response) => response.ok ? response.json() : Promise.reject(response))
            .then(atualizarPainel)
            .catch(() => {
                root.querySelector('[data-iot-status]').textContent = 'Indisponível';
            })
            .finally(() => { if (button) button.disabled = false; });
    }

    root.querySelector('[data-iot-refresh]')?.addEventListener('click', atualizar);
    window.setInterval(atualizar, 15000);
})();