/* JavaScript para pré-checagem de doações */

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('pre-checagem-form');
    const nomeInput = document.getElementById('nome');
    const loteInput = document.getElementById('lote');
    const dataValidadeInput = document.getElementById('data_validade');
    const quantidadeInput = document.getElementById('quantidade');
    const tarjaInput = document.getElementById('tarja');
    const principioAtivoInput = document.getElementById('principio_ativo');

    // Validação básica no lado do cliente (não substitui validação do servidor)
    form.addEventListener('submit', function(e) {
        e.preventDefault();

        // Limpar mensagens de erro anteriores
        limparErros();

        let temErro = false;

        // Validar nome
        if (!nomeInput.value.trim()) {
            mostrarErro(nomeInput, 'Nome do medicamento é obrigatório.');
            temErro = true;
        }

        // Validar lote
        if (!loteInput.value.trim()) {
            mostrarErro(loteInput, 'Número do lote é obrigatório.');
            temErro = true;
        }

        // Validar data de validade
        if (!dataValidadeInput.value) {
            mostrarErro(dataValidadeInput, 'Data de validade é obrigatória.');
            temErro = true;
        } else {
            const dataValidade = new Date(dataValidadeInput.value);
            const hoje = new Date();
            hoje.setHours(0, 0, 0, 0);

            if (dataValidade <= hoje) {
                mostrarErro(dataValidadeInput, 'Data de validade deve ser posterior a hoje.');
                temErro = true;
            }
        }

        // Validar quantidade
        if (!quantidadeInput.value || parseInt(quantidadeInput.value) <= 0) {
            mostrarErro(quantidadeInput, 'Quantidade deve ser maior que zero.');
            temErro = true;
        }

        // Validar tarja
        if (!tarjaInput.value) {
            mostrarErro(tarjaInput, 'Classificação (tarja) é obrigatória.');
            temErro = true;
        }

        // Se não houver erro no cliente, enviar para validação do servidor
        if (!temErro) {
            form.submit();
        }
    });

    // Função para mostrar erro em um campo
    function mostrarErro(input, mensagem) {
        const feedback = document.createElement('div');
        feedback.className = 'invalid-feedback d-block';
        feedback.textContent = mensagem;
        feedback.style.color = '#dc3545';
        feedback.style.fontSize = '0.875rem';
        feedback.style.marginTop = '0.25rem';

        input.classList.add('is-invalid');
        input.parentNode.appendChild(feedback);
    }

    // Função para limpar erros
    function limparErros() {
        const inputs = form.querySelectorAll('input, select');
        inputs.forEach(input => {
            input.classList.remove('is-invalid');
            const feedback = input.parentNode.querySelector('.invalid-feedback');
            if (feedback) {
                feedback.remove();
            }
        });
    }

    // Remover erro ao corrigir o campo
    const inputs = form.querySelectorAll('input, select');
    inputs.forEach(input => {
        input.addEventListener('input', function() {
            this.classList.remove('is-invalid');
            const feedback = this.parentNode.querySelector('.invalid-feedback');
            if (feedback) {
                feedback.remove();
            }
        });
    });

    // Acessibilidade: foco visível
    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.style.outline = '2px solid #0d6efd';
            this.style.outlineOffset = '2px';
        });

        input.addEventListener('blur', function() {
            this.style.outline = '';
            this.style.outlineOffset = '';
        });
    });
});
