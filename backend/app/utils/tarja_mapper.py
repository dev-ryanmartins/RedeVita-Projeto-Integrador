"""
Utilitário para mapeamento automático de tarjas de medicamentos
Baseado em princípios ativos e nomes conforme regulamentação ANVISA
"""


def mapear_tarja_por_principio_ativo(nome_medicamento: str, principio_ativo: str = None) -> str:
    """
    Mapeia automaticamente a tarja com base no princípio ativo ou nome do medicamento.
    Usado para garantir que medicamentos controlados sejam classificados corretamente.
    
    Args:
        nome_medicamento: Nome do medicamento
        principio_ativo: Princípio ativo (opcional)
    
    Returns:
        Tarja classificada (Portaria 344, Tarja Vermelha, Tarja Amarela, Sem Tarja)
    """
    # Normaliza para comparação
    nome_lower = nome_medicamento.lower()
    principio_lower = (principio_ativo or "").lower()
    
    # Lista de princípios ativos controlados por categoria
    # Portaria 344 (Tarja Preta/A1/A2/A3) - Entorpecentes e Psicotrópicos
    portaria_344_keywords = [
        # A1 - Entorpecentes mais rígidos
        'morfina', 'fentanila', 'metadona', 'oxicodona', 'codeína', 'sufentanila',
        'hidromorfona', 'petidina',
        # A2 - Entorpecentes de uso especial
        'tramadol', 'buprenorfina',
        # A3 - Psicotrópicos Notificação A
        'metilfenidato', 'lisdexanfetamina', 'modafinila',
        # B1 - Psicotrópicos com potencial de dependência
        'alprazolam', 'diazepam', 'clonazepam', 'lorazepam', 'bromazepam',
        'nitrazepam', 'midazolam', 'zolpidem', 'zopiclona', 'clobazam',
        'cloxazolam', 'flunitrazepam', 'estazolam', 'oxazepam', 'eszopiclona',
        'alfazolam', 'flurazepam', 'halazepam'
    ]
    
    # Tarja Vermelha - Anti-inflamatórios não esteroides
    tarja_vermelha_keywords = [
        'ibuprofeno', 'naproxeno', 'diclofenaco', 'nimesulida', 'meloxicam',
        'celecoxibe', 'etoricoxibe', 'indometacina', 'piroxicam', 'cetoprofeno',
        'tenoxicam', 'ketorolaco', 'piroxicam', 'indometacina'
    ]
    
    # Tarja Amarela - Antibióticos (requer receita simples)
    tarja_amarela_keywords = [
        'amoxicilina', 'azitromicina', 'ciprofloxacino', 'levofloxacino',
        'claritromicina', 'doxiciclina', 'cefalexina', 'ceftriaxona',
        'cefazolina', 'ampicilina', 'penicilina'
    ]
    
    # Verifica Portaria 344 (controle especial)
    for keyword in portaria_344_keywords:
        if keyword in principio_lower or keyword in nome_lower:
            return "Portaria 344"
    
    # Verifica Tarja Vermelha
    for keyword in tarja_vermelha_keywords:
        if keyword in principio_lower or keyword in nome_lower:
            return "Tarja Vermelha"
    
    # Verifica Tarja Amarela
    for keyword in tarja_amarela_keywords:
        if keyword in principio_lower or keyword in nome_lower:
            return "Tarja Amarela"
    
    # Padrão: Sem Tarja
    return "Sem Tarja"
