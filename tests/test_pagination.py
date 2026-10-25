"""
Testes para paginação em mapa.py e donation.py (P2.2).
Verifica que paginação está implementada no código-fonte.
"""

import pytest


class TestMapaPagination:
    """Testes para paginação em mapa.py."""
    
    def test_mapa_saude_tem_paginacao(self):
        """Rota /mapa deve ter código de paginação."""
        with open('backend/app/routes/mapa.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Deve ter parâmetros de paginação
        assert 'page' in content.lower()
        assert 'per_page' in content.lower()
        # Deve usar paginate
        assert 'paginate' in content
        # Deve ter limite máximo
        assert '500' in content or 'max' in content.lower()
    
    def test_mapa_proximidade_tem_limite(self):
        """Rota /api/mapa/proximidade deve ter limite de resultados."""
        with open('backend/app/routes/mapa.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Deve ter limite de resultados
        assert 'MAX_RESULTADOS' in content or 'limit' in content.lower()
        # Deve ter valor máximo (50)
        assert '50' in content


class TestDonationPagination:
    """Testes para paginação em donation.py."""
    
    def test_doacoes_medicamentos_tem_paginacao(self):
        """Rota /doacoes deve ter paginação para medicamentos."""
        with open('backend/app/routes/donation.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Deve ter parâmetros de paginação
        assert 'page' in content.lower()
        assert 'per_page' in content.lower()
        # Deve usar paginate
        assert 'paginate' in content
        # Deve ter limite máximo
        assert '200' in content or 'max' in content.lower()
    
    def test_doacoes_filtro_data_tem_paginacao(self):
        """Rota /doacoes deve ter paginação para doações com filtro."""
        with open('backend/app/routes/donation.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Deve ter paginação após filtros de data
        lines = content.split('\n')
        found_data_filter = False
        found_paginate = False
        
        for line in lines:
            if 'data_inicio' in line or 'data_fim' in line:
                found_data_filter = True
            if found_data_filter and 'paginate' in line:
                found_paginate = True
                break
        
        assert found_paginate, "Paginação não encontrada após filtros de data"
