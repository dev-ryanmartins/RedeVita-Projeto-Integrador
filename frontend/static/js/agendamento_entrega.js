/* JavaScript para Agendamento de Entrega */

document.addEventListener('DOMContentLoaded', function() {
    // Validação básica no formulário
    const form = document.querySelector('form[method="POST"]');
    if (form) {
        form.addEventListener('submit', function(e) {
            const farmaciaOrigem = document.getElementById('farmacia_origem_id').value;
            const farmaciaDestino = document.getElementById('farmacia_destino_id').value;
            const dataInicio = document.getElementById('data_hora_inicio').value;
            const dataFim = document.getElementById('data_hora_fim').value;
            
            if (!farmaciaOrigem || !farmaciaDestino) {
                e.preventDefault();
                alert('Farmácias de origem e destino são obrigatórias.');
                return;
            }
            
            if (farmaciaOrigem === farmaciaDestino) {
                e.preventDefault();
                alert('Farmácia de origem e destino devem ser diferentes.');
                return;
            }
            
            if (!dataInicio || !dataFim) {
                e.preventDefault();
                alert('Data e hora são obrigatórias.');
                return;
            }
            
            const inicio = new Date(dataInicio);
            const fim = new Date(dataFim);
            const agora = new Date();
            
            if (inicio <= agora) {
                e.preventDefault();
                alert('Data/hora não pode estar no passado.');
                return;
            }
            
            if (fim <= inicio) {
                e.preventDefault();
                alert('Data/hora fim deve ser posterior à início.');
                return;
            }
        });
    }
    
    // Melhorar UX nos filtros
    const filterButtons = document.querySelectorAll('form[method="GET"] button');
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            this.disabled = true;
            this.textContent = 'Filtrando...';
        });
    });
});
