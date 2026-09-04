"""
Trie Search - Estrutura de Dados Árvore Trie (Prefix Tree)
Implementa autocompletar eficiente para busca de medicamentos e princípios ativos
Complexidade de tempo: O(K) onde K é o tamanho do termo digitado
Disciplina: Estruturas de Dados - Árvores e Grafos
"""

from typing import Dict, List, Optional, Set
from app.models.medicamento import Medicamento


class TrieNode:
    """
    Nó da Árvore Trie.
    Cada nó contém filhos e um indicador se é o fim de uma palavra.
    """
    
    def __init__(self):
        self.filhos: Dict[str, 'TrieNode'] = {}
        self.eh_fim_palavra: bool = False
        self.medicamentos_ids: Set[int] = set()  # IDs de medicamentos que contêm este prefixo


class Trie:
    """
    Estrutura de Dados Trie (Prefix Tree) para busca eficiente por prefixo.
    Permite autocompletar com complexidade O(K) onde K é o tamanho do prefixo.
    """
    
    def __init__(self):
        self.raiz = TrieNode()
        self._carregada = False
    
    def inserir(self, palavra: str, medicamento_id: int):
        """
        Insere uma palavra na Trie.
        
        Args:
            palavra: Palavra a inserir (normalizada para minúsculas)
            medicamento_id: ID do medicamento associado
        """
        palavra = palavra.lower().strip()
        if not palavra:
            return
        
        no = self.raiz
        for caractere in palavra:
            if caractere not in no.filhos:
                no.filhos[caractere] = TrieNode()
            no = no.filhos[caractere]
            no.medicamentos_ids.add(medicamento_id)
        
        no.eh_fim_palavra = True
    
    def buscar_prefixo(self, prefixo: str) -> List[str]:
        """
        Busca todas as palavras que começam com o prefixo.
        
        Args:
            prefixo: Prefixo para buscar
        
        Returns:
            Lista de palavras que começam com o prefixo
        """
        prefixo = prefixo.lower().strip()
        if not prefixo:
            return []
        
        no = self.raiz
        for caractere in prefixo:
            if caractere not in no.filhos:
                return []
            no = no.filhos[caractere]
        
        # Encontra todas as palavras a partir deste nó
        palavras = []
        self._coletar_palavras(no, prefixo, palavras)
        return palavras
    
    def buscar_ids_por_prefixo(self, prefixo: str) -> Set[int]:
        """
        Busca todos os IDs de medicamentos que contêm o prefixo.
        
        Args:
            prefixo: Prefixo para buscar
        
        Returns:
            Conjunto de IDs de medicamentos
        """
        prefixo = prefixo.lower().strip()
        if not prefixo:
            return set()
        
        no = self.raiz
        for caractere in prefixo:
            if caractere not in no.filhos:
                return set()
            no = no.filhos[caractere]
        
        return no.medicamentos_ids.copy()
    
    def _coletar_palavras(self, no: TrieNode, prefixo: str, resultado: List[str]):
        """
        Coleta recursivamente todas as palavras a partir de um nó.
        """
        if no.eh_fim_palavra:
            resultado.append(prefixo)
        
        for caractere, filho in sorted(no.filhos.items()):
            self._coletar_palavras(filho, prefixo + caractere, resultado)
    
    def carregar_medicamentos(self):
        """
        Carrega todos os medicamentos do banco de dados na Trie.
        Popula a Trie com nomes e princípios ativos.
        """
        if self._carregada:
            return
        
        medicamentos = Medicamento.query.all()
        
        for med in medicamentos:
            if med.nome:
                self.inserir(med.nome, med.id)
            if med.principio_ativo:
                self.inserir(med.principio_ativo, med.id)
        
        self._carregada = True
    
    def recarregar(self):
        """
        Recarrega a Trie com dados atualizados do banco.
        """
        self.raiz = TrieNode()
        self._carregada = False
        self.carregar_medicamentos()


# Instância global da Trie
_trie_medicamentos: Optional[Trie] = None


def obter_trie_medicamentos() -> Trie:
    """
    Obtém a instância global da Trie de medicamentos.
    Lazy loading - carrega apenas na primeira chamada.
    
    Returns:
        Instância da Trie carregada com medicamentos
    """
    global _trie_medicamentos
    
    if _trie_medicamentos is None:
        _trie_medicamentos = Trie()
        _trie_medicamentos.carregar_medicamentos()
    
    return _trie_medicamentos


def autocompletar_medicamentos(prefixo: str, limite: int = 10) -> List[Dict]:
    """
    Função de autocompletar para medicamentos.
    Retorna sugestões baseadas no prefixo digitado.
    
    Args:
        prefixo: Prefixo digitado pelo usuário
        limite: Número máximo de sugestões
    
    Returns:
        Lista de dicts com sugestões de medicamentos
    """
    if len(prefixo) < 2:
        return []
    
    trie = obter_trie_medicamentos()
    ids_medicamentos = trie.buscar_ids_por_prefixo(prefixo)
    
    if not ids_medicamentos:
        return []
    
    # Busca medicamentos no banco
    medicamentos = Medicamento.query.filter(
        Medicamento.id.in_(ids_medicamentos)
    ).limit(limite).all()
    
    return [
        {
            'id': med.id,
            'nome': med.nome,
            'principio_ativo': med.principio_ativo,
            'lote': med.lote,
            'quantidade': med.quantidade
        }
        for med in medicamentos
    ]


def autocompletar_nomes(prefixo: str, limite: int = 10) -> List[str]:
    """
    Função de autocompletar apenas para nomes de medicamentos.
    
    Args:
        prefixo: Prefixo digitado
        limite: Número máximo de sugestões
    
    Returns:
        Lista de nomes de medicamentos
    """
    if len(prefixo) < 2:
        return []
    
    trie = obter_trie_medicamentos()
    palavras = trie.buscar_prefixo(prefixo)
    
    return palavras[:limite]


def invalidar_cache_trie():
    """
    Invalida o cache da Trie, forçando recarga na próxima chamada.
    Útil após inserir/atualizar medicamentos.
    """
    global _trie_medicamentos
    _trie_medicamentos = None
