"""Índice Trie para sugestões rápidas sem alterar a busca global existente.

O índice é construído a partir dos registros recebidos pela chamada. Assim, a
função não mantém referências obsoletas aos objetos do SQLAlchemy e pode ser
usada com qualquer fonte de dados no futuro.
"""

import re
import unicodedata
from collections import defaultdict
from typing import Any, Iterable


def normalizar_termo(valor: Any) -> str:
    """Normaliza acentos, caixa e espaços para comparação consistente."""
    texto = str(valor or "").strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(caractere for caractere in texto if not unicodedata.combining(caractere))
    return re.sub(r"\s+", " ", texto)


class TrieNode:
    """Nó interno de uma Trie, com referências aos registros encontrados."""

    __slots__ = ("filhos", "valores")

    def __init__(self) -> None:
        self.filhos: dict[str, "TrieNode"] = {}
        self.valores: list[str] = []


class TrieIndex:
    """Índice de prefixos com inserção O(k) e consulta O(k + r)."""

    def __init__(self) -> None:
        self.raiz = TrieNode()
        self._valores: dict[str, Any] = {}

    def adicionar(self, termo: Any, valor: Any, chave: str) -> None:
        termo_normalizado = normalizar_termo(termo)
        chave = str(chave)
        if not termo_normalizado:
            return

        self._valores.setdefault(chave, valor)
        node = self.raiz
        for caractere in termo_normalizado:
            node = node.filhos.setdefault(caractere, TrieNode())
            if chave not in node.valores:
                node.valores.append(chave)

    def buscar(self, prefixo: Any, limite: int = 20) -> list[Any]:
        prefixo_normalizado = normalizar_termo(prefixo)
        if not prefixo_normalizado or limite <= 0:
            return []

        node = self.raiz
        for caractere in prefixo_normalizado:
            node = node.filhos.get(caractere)
            if node is None:
                return []

        return [self._valores[chave] for chave in node.valores[:limite]]


def _adicionar_com_tokens(index: TrieIndex, texto: str, valor: Any, chave: str) -> None:
    """Indexa a expressão completa e também seus tokens para autocomplete."""
    index.adicionar(texto, valor, chave)
    for token in re.findall(r"[\wÀ-ÿ]+", str(texto or "")):
        index.adicionar(token, valor, chave)


def buscar_entidades_rapida(
    query: str,
    medicamentos: Iterable[Any] = (),
    pacientes: Iterable[Any] = (),
    limite: int = 20,
) -> list[dict[str, Any]]:
    """Retorna sugestões de medicamentos e pacientes por prefixo."""
    index = TrieIndex()

    for medicamento in medicamentos:
        valor = {
            "tipo": "medicamento",
            "id": medicamento.id,
            "label": medicamento.nome,
            "detalhe": medicamento.principio_ativo or medicamento.lote or "Medicamento",
        }
        chave = f"medicamento:{medicamento.id}"
        _adicionar_com_tokens(index, medicamento.nome, valor, chave)
        _adicionar_com_tokens(index, medicamento.principio_ativo, valor, chave)
        _adicionar_com_tokens(index, medicamento.lote, valor, chave)

    for paciente in pacientes:
        valor = {
            "tipo": "paciente",
            "id": paciente.id,
            "label": paciente.nome,
            "detalhe": f"CPF {paciente.cpf}",
        }
        chave = f"paciente:{paciente.id}"
        _adicionar_com_tokens(index, paciente.nome, valor, chave)
        _adicionar_com_tokens(index, paciente.cpf, valor, chave)

    return index.buscar(query, limite)