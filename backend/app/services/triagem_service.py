"""
Serviço de domínio para triagem de medicamentos.
Extrai lógica de negócio comum entre donation.py e api.py.
"""

from datetime import datetime
from typing import Tuple, Dict, Any, Optional

from app.models.medicamento import Medicamento
from app.utils.semaforo import calcular_status_semaforo


TARJAS_VALIDAS = ["Sem Tarja", "Tarja Amarela", "Tarja Vermelha", "Portaria 344"]
CONTROLLED_KEYWORDS = [
    'antibiotico', 'antidepressivo', 'anfetamina', 'opiaceo',
    'benzodiazepin', 'controlado', 'psicotropico'
]


class TriagemError(Exception):
    """Erro de validação na triagem de medicamento."""
    def __init__(self, mensagem: str, campo: Optional[str] = None):
        self.mensagem = mensagem
        self.campo = campo
        super().__init__(mensagem)


class TriagemMedicamentoService:
    """Serviço para validação e criação de medicamentos via triagem."""
    
    @staticmethod
    def validar_entrada(
        nome: str,
        lote: str,
        data_validade_str: str,
        quantidade_str: str,
        tarja: str = "Sem Tarja",
        principio_ativo: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Valida os dados de entrada para triagem de medicamento.
        
        Args:
            nome: Nome do medicamento
            lote: Número do lote
            data_validade_str: Data de validade em formato YYYY-MM-DD
            quantidade_str: Quantidade como string
            tarja: Tipo de tarja (default: Sem Tarja)
            principio_ativo: Princípio ativo (opcional)
        
        Returns:
            Tuple (valido, erro_mensagem, dados_validados)
            
        Raises:
            TriagemError: Se houver erro de validação
        """
        # Validar campos obrigatórios
        if not nome or not lote or not data_validade_str or not quantidade_str:
            raise TriagemError("Preencha todos os campos obrigatórios.", "campos_obrigatorios")
        
        # Validar quantidade
        try:
            quantidade = int(quantidade_str)
            if quantidade <= 0:
                raise TriagemError("Quantidade inválida. Informe um número inteiro positivo.", "quantidade")
        except ValueError:
            raise TriagemError("Quantidade inválida.", "quantidade")
        
        # Validar data de validade
        try:
            data_validade = datetime.strptime(data_validade_str, "%Y-%m-%d").date()
        except ValueError:
            raise TriagemError("Data de validade inválida.", "data_validade")
        
        # Normalizar tarja
        if tarja not in TARJAS_VALIDAS:
            tarja = "Sem Tarja"
        
        dados_validados = {
            "nome": nome,
            "lote": lote,
            "data_validade": data_validade,
            "quantidade": quantidade,
            "tarja": tarja,
            "principio_ativo": principio_ativo,
        }
        
        return True, None, dados_validados
    
    @staticmethod
    def validar_regras_negocio(dados: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Valida regras de negócio para triagem de medicamento.
        
        Args:
            dados: Dicionário com dados validados do medicamento
        
        Returns:
            Tuple (valido, erro_mensagem)
            
        Raises:
            TriagemError: Se houver violação de regra de negócio
        """
        data_validade = dados["data_validade"]
        tarja = dados["tarja"]
        principio_ativo = dados.get("principio_ativo", "")
        
        # Calcular status do semáforo
        status = calcular_status_semaforo(data_validade)
        
        # Bloquear medicamentos vencidos
        if status == 2:
            raise TriagemError(
                "ERRO BLOQUEANTE: Não é possível cadastrar medicamentos vencidos (status Vermelho). "
                "Medicamento fora da validade regulatória.",
                "data_validade"
            )
        
        # Bloquear Portaria 344
        if tarja == "Portaria 344":
            raise TriagemError(
                "ERRO BLOQUEANTE: Substâncias controladas pela Portaria 344 não podem ser cadastradas "
                "automaticamente. Requer validação manual do farmacêutico responsável.",
                "tarja"
            )
        
        # Bloquear princípios ativos controlados por heurística
        principio_lower = (principio_ativo or "").lower()
        if any(keyword in principio_lower for keyword in CONTROLLED_KEYWORDS):
            raise TriagemError(
                "ERRO BLOQUEANTE: Substâncias controladas detectadas pelo princípio ativo. "
                "Requer validação manual do farmacêutico responsável.",
                "principio_ativo"
            )
        
        dados["status_semaforo"] = status
        return True, None
    
    @staticmethod
    def criar_medicamento(dados: Dict[str, Any]) -> Medicamento:
        """
        Cria uma instância de Medicamento com os dados validados.
        
        Args:
            dados: Dicionário com dados validados do medicamento
        
        Returns:
            Instância de Medicamento
        """
        med = Medicamento(
            nome=dados["nome"],
            lote=dados["lote"],
            data_validade=dados["data_validade"],
            quantidade=dados["quantidade"],
            status_semaforo=dados["status_semaforo"],
            tarja=dados["tarja"],
            principio_ativo=dados.get("principio_ativo"),
        )
        
        # Validar Portaria 344 no modelo
        is_valid, error_msg = med.validar_portaria_344()
        if not is_valid:
            raise TriagemError(f"Erro de validação ANVISA: {error_msg}", "portaria_344")
        
        return med
    
    @staticmethod
    def processar_triagem(
        nome: str,
        lote: str,
        data_validade_str: str,
        quantidade_str: str,
        tarja: str = "Sem Tarja",
        principio_ativo: Optional[str] = None,
        doador: Optional[str] = None,
        observacoes: Optional[str] = None
    ) -> Tuple[Medicamento, str]:
        """
        Processa o fluxo completo de triagem de medicamento.
        
        Args:
            nome: Nome do medicamento
            lote: Número do lote
            data_validade_str: Data de validade em formato YYYY-MM-DD
            quantidade_str: Quantidade como string
            tarja: Tipo de tarja (default: Sem Tarja)
            principio_ativo: Princípio ativo (opcional)
            doador: Nome do doador (opcional)
            observacoes: Observações (opcional)
        
        Returns:
            Tuple (medicamento_criado, mensagem_aviso)
            
        Raises:
            TriagemError: Se houver erro de validação
        """
        # Validar entrada
        valido, erro, dados = TriagemMedicamentoService.validar_entrada(
            nome, lote, data_validade_str, quantidade_str, tarja, principio_ativo
        )
        if not valido:
            raise TriagemError(erro)
        
        # Validar regras de negócio
        valido, erro = TriagemMedicamentoService.validar_regras_negocio(dados)
        if not valido:
            raise TriagemError(erro)
        
        # Criar medicamento
        medicamento = TriagemMedicamentoService.criar_medicamento(dados)
        
        # Gerar mensagem de aviso baseada no status
        status = dados["status_semaforo"]
        if status == 2:
            aviso = f'"{nome}" adicionado, mas atenção: o lote está VENCIDO.'
        elif status == 1:
            aviso = f'"{nome}" adicionado ao estoque. Lote próximo ao vencimento.'
        else:
            aviso = f'"{nome}" validado e adicionado ao estoque com sucesso!'
        
        return medicamento, aviso
    
    @staticmethod
    def obter_tarjas_validas() -> list:
        """Retorna lista de tarjas válidas."""
        return TARJAS_VALIDAS.copy()
