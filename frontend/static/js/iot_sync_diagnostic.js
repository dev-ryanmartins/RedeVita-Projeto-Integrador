// IoT Sync Diagnostic - Frontend JavaScript
// Handles data fetching, filtering, pagination, and display

document.addEventListener('DOMContentLoaded', function() {
    const MAX_PAGE_SIZE = 50;
    const DEFAULT_PAGE_SIZE = 20;
    
    let currentPage = 1;
    let currentFilters = {};
    
    // DOM elements
    const dataInicioInput = document.getElementById('data-inicio');
    const dataFimInput = document.getElementById('data-fim');
    const resultadoFiltro = document.getElementById('resultado-filtro');
    const dispositivoFiltro = document.getElementById('dispositivo-filtro');
    const aplicarFiltrosBtn = document.getElementById('aplicar-filtros');
    const limparFiltrosBtn = document.getElementById('limpar-filtros');
    const lotesTbody = document.getElementById('lotes-tbody');
    const prevPageBtn = document.getElementById('prev-page');
    const nextPageBtn = document.getElementById('next-page');
    const pageInfo = document.getElementById('page-info');
    const emptyState = document.getElementById('empty-state');
    const errorState = document.getElementById('error-state');
    const loadingState = document.getElementById('loading-state');
    const retryButton = document.getElementById('retry-button');
    
    // Initialize default date range (last 7 days)
    const hoje = new Date();
    const seteDiasAtras = new Date(hoje);
    seteDiasAtras.setDate(hoje.getDate() - 7);
    
    dataInicioInput.value = seteDiasAtras.toISOString().split('T')[0];
    dataFimInput.value = hoje.toISOString().split('T')[0];
    
    // Load dispositivos
    loadDispositivos();
    
    // Load initial data
    loadLotes();
    
    // Event listeners
    aplicarFiltrosBtn.addEventListener('click', applyFilters);
    limparFiltrosBtn.addEventListener('click', clearFilters);
    prevPageBtn.addEventListener('click', () => loadLotes(currentPage - 1));
    nextPageBtn.addEventListener('click', () => loadLotes(currentPage + 1));
    retryButton.addEventListener('click', loadLotes);
    
    // Handle visibility API to pause auto-refresh if needed
    document.addEventListener('visibilitychange', () => {
        if (!document.hidden) {
            loadLotes(currentPage);
        }
    });
    
    function loadDispositivos() {
        fetch('/api/admin/diagnostico-iot/dispositivos')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'ok' && data.dispositivos) {
                    data.dispositivos.forEach(dispositivo => {
                        const option = document.createElement('option');
                        option.value = dispositivo;
                        option.textContent = dispositivo;
                        dispositivoFiltro.appendChild(option);
                    });
                }
            })
            .catch(error => {
                console.error('Erro ao carregar dispositivos:', error);
            });
    }
    
    function applyFilters() {
        currentPage = 1;
        currentFilters = {
            data_inicio: dataInicioInput.value,
            data_fim: dataFimInput.value,
            resultado: resultadoFiltro.value,
            dispositivo: dispositivoFiltro.value
        };
        loadLotes();
    }
    
    function clearFilters() {
        dataInicioInput.value = seteDiasAtras.toISOString().split('T')[0];
        dataFimInput.value = hoje.toISOString().split('T')[0];
        resultadoFiltro.value = '';
        dispositivoFiltro.value = '';
        currentFilters = {};
        currentPage = 1;
        loadLotes();
    }
    
    function loadLotes(page = 1) {
        showLoading();
        
        const params = new URLSearchParams({
            page: page,
            page_size: DEFAULT_PAGE_SIZE,
            ...currentFilters
        });
        
        fetch(`/api/admin/diagnostico-iot/dados?${params}`)
            .then(response => response.json())
            .then(data => {
                hideLoading();
                
                if (data.status === 'ok') {
                    displayLotes(data);
                } else {
                    showError('Erro ao carregar dados: ' + (data.mensagem || 'Desconhecido'));
                }
            })
            .catch(error => {
                hideLoading();
                showError('Erro de rede ao carregar dados');
                console.error('Erro:', error);
            });
    }
    
    function displayLotes(data) {
        const lotes = data.lotes || [];
        const paginacao = data.paginacao || {};
        const agregados = data.agregados || {};
        
        // Update indicators
        document.getElementById('total-lotes').textContent = agregados.total_lotes || 0;
        document.getElementById('total-recebidas').textContent = agregados.total_recebidas || 0;
        document.getElementById('total-processadas').textContent = agregados.total_processadas || 0;
        document.getElementById('total-rejeitadas').textContent = agregados.total_rejeitadas || 0;
        
        // Update distribution bars
        const contagemPorResultado = agregados.contagem_por_resultado || {};
        const total = agregados.total_lotes || 1;
        
        const completoCount = contagemPorResultado.COMPLETO || 0;
        const parcialCount = contagemPorResultado.PARCIAL || 0;
        const rejeitadoCount = contagemPorResultado.REJEITADO || 0;
        
        document.getElementById('bar-completo').style.width = (completoCount / total * 100) + '%';
        document.getElementById('val-completo').textContent = completoCount;
        
        document.getElementById('bar-parcial').style.width = (parcialCount / total * 100) + '%';
        document.getElementById('val-parcial').textContent = parcialCount;
        
        document.getElementById('bar-rejeitado').style.width = (rejeitadoCount / total * 100) + '%';
        document.getElementById('val-rejeitado').textContent = rejeitadoCount;
        
        // Update table
        lotesTbody.innerHTML = '';
        
        if (lotes.length === 0) {
            showEmpty();
            return;
        }
        
        lotes.forEach(lote => {
            const row = document.createElement('tr');
            
            const dataRecebimento = lote.data_recebimento 
                ? new Date(lote.data_recebimento).toLocaleString('pt-BR', { timeZone: 'UTC' }) 
                : '-';
            
            const resultadoClass = `status-${lote.resultado.toLowerCase()}`;
            
            row.innerHTML = `
                <td>${dataRecebimento}</td>
                <td><code>${lote.lote_id.substring(0, 8)}...</code></td>
                <td><span class="status-badge ${resultadoClass}">${lote.resultado}</span></td>
                <td>${lote.total_recebidas}</td>
                <td>${lote.total_processadas}</td>
                <td>${lote.total_rejeitadas}</td>
                <td>${lote.qtd_dispositivos}</td>
                <td>${lote.dispositivo_principal || '<em>Misto</em>'}</td>
            `;
            
            lotesTbody.appendChild(row);
        });
        
        // Update pagination
        currentPage = paginacao.page || 1;
        pageInfo.textContent = `Página ${currentPage} de ${paginacao.pages || 1}`;
        prevPageBtn.disabled = !paginacao.has_prev;
        nextPageBtn.disabled = !paginacao.has_next;
        
        // Show table, hide empty/error
        emptyState.style.display = 'none';
        errorState.style.display = 'none';
        document.querySelector('.table-section').style.display = 'block';
    }
    
    function showLoading() {
        loadingState.style.display = 'block';
        emptyState.style.display = 'none';
        errorState.style.display = 'none';
        document.querySelector('.table-section').style.display = 'none';
    }
    
    function hideLoading() {
        loadingState.style.display = 'none';
    }
    
    function showEmpty() {
        emptyState.style.display = 'block';
        errorState.style.display = 'none';
        document.querySelector('.table-section').style.display = 'none';
    }
    
    function showError(message) {
        errorState.style.display = 'block';
        document.getElementById('error-message').textContent = message;
        emptyState.style.display = 'none';
        document.querySelector('.table-section').style.display = 'none';
    }
});
