"""
Serviço FEFO (First Expired, First Out) para sugestão de lotes.

Sugere lotes elegíveis ordenados por data de validade crescente.
"""

from app.database import db
from app.models.medicamento import Medicamento
from app.services.ledger_estoque import LedgerEstoqueService
from datetime import date, timedelta
from typing import List, Dict, Optional


class FefoService:
    """Serviço para sugestão FEFO de lotes."""
    
    @staticmethod
    def sugerir_lotes(
        medicamento_nome: str,
        quantidade_necessaria: int,
        incluir_vencidos: bool = False
    ) -> List[Dict]:
        """
        Sugere lotes elegíveis ordenados por validade crescente (FEFO).
        
        Args:
            medicamento_nome: Nome do medicamento para buscar lotes
            quantidade_necessaria: Quantidade necessária para a operação
            incluir_vencidos: Se deve incluir lotes vencidos (default: False)
            
        Returns:
            Lista de lotes sugeridos com informações relevantes
        """
        # Buscar lotes do medicamento
        query = Medicamento.query.filter(
            Medicamento.nome.ilike(f"%{medicamento_nome}%"),
            Medicamento.ativo == True
        )
        
        # Excluir vencidos se não solicitado
        if not incluir_vencidos:
            query = query.filter(Medicamento.status_semaforo != 2)
        
        # Excluir lotes sem saldo
        query = query.filter(Medicamento.quantidade > 0)
        
        lotes = query.all()
        
        # Ordenar por validade crescente (FEFO)
        lotes_ordenados = sorted(lotes, key=lambda m: m.data_validade)
        
        # Construir lista de sugestões
        sugestoes = []
        for lote in lotes_ordenados:
            # Calcular saldo derivado do ledger
            saldo_ledger = LedgerEstoqueService.calcular_saldo_derivado(lote.id)
            
            # Verificar elegibilidade
            if saldo_ledger <= 0:
                continue  # Pular lotes sem saldo no ledger
            
            # Calcular dias para vencer
            dias_para_vencer = (lote.data_validade - date.today()).days
            
            sugestao = {
                'medicamento_id': lote.id,
                'nome': lote.nome,
                'lote': lote.lote,
                'data_validade': lote.data_validade.isoformat(),
                'dias_para_vencer': dias_para_vencer,
                'quantidade_disponivel': saldo_ledger,
                'quantidade_sistema': lote.quantidade,
                'status_semaforo': lote.status_semaforo,
                'tarja': lote.tarja,
                'controlado': lote.controlado,
                'elegivel': saldo_ledger >= quantidade_necessaria and dias_para_vencer >= 0
            }
            
            sugestoes.append(sugestao)
        
        return sugestoes
    
    @staticmethod
    def obter_melhor_lote(
        medicamento_nome: str,
        quantidade_necessaria: int,
        incluir_vencidos: bool = False
    ) -> Optional[Dict]:
        """
        Retorna o melhor lote (primeiro na ordem FEFO) ou None.
        
        Args:
            medicamento_nome: Nome do medicamento
            quantidade_necessaria: Quantidade necessária
            incluir_vencidos: Se deve incluir lotes vencidos
            
        Returns:
            Dict com informações do melhor lote ou None
        """
        sugestoes = FefoService.sugerir_lotes(
            medicamento_nome=medicamento_nome,
            quantidade_necessaria=quantidade_necessaria,
            incluir_vencidos=incluir_vencidos
        )
        
        if not sugestoes:
            return None
        
        # Retornar o primeiro (mais próximo do vencimento)
        return sugestoes[0]
    
    @staticmethod
    def validar_lote_antes_operacao(
        medicamento_id: int,
        quantidade_necessaria: int,
        operacao_id: Optional[str] = None
    ) -> Dict:
        """
        Revalida um lote antes de executar a operação.
        
        Verifica se o lote ainda é elegível e tem saldo suficiente.
        Se houver mudança desde a sugestão, recusa a operação.
        
        Args:
            medicamento_id: ID do medicamento/lote
            quantidade_necessaria: Quantidade necessária
            operacao_id: ID da operação para idempotência
            
        Returns:
            Dict com resultado da validação
        """
        medicamento = Medicamento.query.get(medicamento_id)
        
        if not medicamento:
            return {
                'valido': False,
                'motivo': 'Lote não encontrado'
            }
        
        # Calcular saldo atual do ledger
        saldo_ledger = LedgerEstoqueService.calcular_saldo_derivado(medicamento_id)
        
        # Verificar saldo suficiente
        if saldo_ledger < quantidade_necessaria:
            return {
                'valido': False,
                'motivo': f'Saldo insuficiente. Disponível: {saldo_ledger}, Necessário: {quantidade_necessaria}'
            }
        
        # Verificar validade
        dias_para_vencer = (medicamento.data_validade - date.today()).days
        if dias_para_vencer < 0:
            return {
                'valido': False,
                'motivo': f'Lote vencido em {medicamento.data_validade}'
            }
        
        # Verificar status (se não vencido mas status é vermelho)
        if medicamento.status_semaforo == 2:
            return {
                'valido': False,
                'motivo': 'Lote marcado como vencido no sistema'
            }
        
        # Lote ainda é válido
        return {
            'valido': True,
            'motivo': 'Lote válido e com saldo suficiente',
            'saldo_atual': saldo_ledger,
            'dias_para_vencer': dias_para_vencer
        }
