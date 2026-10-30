/* JavaScript para Quadro de Necessidades de Instituições */

document.addEventListener('DOMContentLoaded', function() {
    // Validação básica no formulário
    const form = document.querySelector('form[method="POST"]');
    if (form) {
        form.addEventListener('submit', function(e) {
            const nomeInstituicao = document.getElementById('nome_instituicao').value.trim();
            const produtoDescritivo = document.getElementById('produto_descritivo').value.trim();
            const medicamentoReferencia = document.getElementById('medicamento_referencia_id').value;
            const quantidade = document.getElementById('quantidade_solicitada').value;
            
            if (!nomeInstituicao) {
                e.preventDefault();
                alert('Nome da instituição é obrigatório.');
                return;
            }
            
            if (!produtoDescritivo && !medicamentoReferencia) {
                e.preventDefault();
                alert('Informe o produto (referência ou descritivo).');
                return;
            }
            
            if (!quantidade || quantidade <= 0) {
                e.preventDefault();
                alert('Quantidade deve ser maior que zero.');
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
