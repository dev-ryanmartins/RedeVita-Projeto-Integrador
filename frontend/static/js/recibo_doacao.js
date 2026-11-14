// Recibo de Etapas da Doação - JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Validação básica no cliente (não substitui validação do servidor)
    console.log('Recibo de Etapas da Doação carregado');

    // Adiciona classe para indicar que a página está pronta
    document.body.classList.add('recibo-doacao-loaded');

    // Melhora acessibilidade com aria-live para notificações dinâmicas
    const alertWarning = document.querySelector('.alert-warning');
    if (alertWarning) {
        alertWarning.setAttribute('role', 'alert');
        alertWarning.setAttribute('aria-live', 'polite');
    }

    // Adiciona tooltips ou comportamentos adicionais se necessário
    const timelineItems = document.querySelectorAll('.timeline-item');
    timelineItems.forEach(item => {
        item.setAttribute('tabindex', '0');
        item.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.classList.toggle('expanded');
            }
        });
    });
});
