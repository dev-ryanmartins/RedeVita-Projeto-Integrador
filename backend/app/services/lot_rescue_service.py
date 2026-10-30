"""
Serviço de simulação de resgate de lotes.

Este serviço simula cenários de planejamento para verificar se há margem
de tempo entre a validade de um lote e a duração de etapas hipotéticas.

LIMITAÇÕES:
- Não usa LedgerEstoqueService (módulo não existe no repositório)
- Usa apenas quantidade cadastrada no modelo Medicamento (não derivada)
- Não calcula distâncias ou rotas (coordenadas podem ser nulas)
- Não vincula lotes a farmácias (sem vínculo no modelo)
- Não associa leituras IoT a lotes (sem relação direta)
- Todas as decisões são hipotéticas e não substituem avaliação farmacêutica
"""

from datetime import date, timedelta
from typing import List, Dict, Optional, Any
from app.database import db
from app.models.medicamento import Medicamento


class LotRescueService:
    """Serviço de simulação de resgate de lotes."""

    # Limites de parâmetros
    MAX_HORIZE_DIAS = 365  # Máximo de 1 ano de horizonte
    MIN_HORIZE_DIAS = 1
    MAX_ETAPA_DIAS = 90  # Máximo de 90 dias por etapa
    MIN_ETAPA_DIAS = 1
    MAX_ETAPAS = 5  # Máximo de 5 etapas simultâneas

    def __init__(self):
        """Inicializa o serviço."""
        pass

    def listar_lotes_para_resgate(
        self,
        horizon_dias: int = 30,
        nome_medicamento: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Lista lotes ativos com validade dentro do horizonte especificado.

        Args:
            horizon_dias: Horizonte em dias para buscar lotes (1-365)
            nome_medicamento: Filtro opcional por nome do medicamento

        Returns:
            Lista de lotes com informações relevantes para simulação
        """
        # Validar horizonte
        if horizon_dias < self.MIN_HORIZE_DIAS or horizon_dias > self.MAX_HORIZE_DIAS:
            raise ValueError(f"Horizonte deve ser entre {self.MIN_HORIZE_DIAS} e {self.MAX_HORIZE_DIAS} dias")

        # Calcular data limite
        data_limite = date.today() + timedelta(days=horizon_dias)

        # Query base
        query = Medicamento.query.filter(
            Medicamento.ativo == True,
            Medicamento.data_validade <= data_limite,
            Medicamento.data_validade >= date.today()
        )

        # Filtro opcional por nome
        if nome_medicamento:
            query = query.filter(Medicamento.nome.ilike(f"%{nome_medicamento}%"))

        lotes = query.all()

        # Construir lista de lotes
        lotes_para_resgate = []
        for lote in lotes:
            dias_para_vencer = (lote.data_validade - date.today()).days

            lotes_para_resgate.append({
                'id': lote.id,
                'nome': lote.nome,
                'lote': lote.lote,
                'data_validade': lote.data_validade.isoformat(),
                'dias_para_vencer': dias_para_vencer,
                'quantidade_cadastrada': lote.quantidade,
                'status_semaforo': lote.status_semaforo,
                'tarja': lote.tarja,
                'controlado': lote.controlado,
                'principio_ativo': lote.principio_ativo
            })

        # Ordenar por dias para vencer (mais críticos primeiro)
        lotes_para_resgate.sort(key=lambda x: x['dias_para_vencer'])

        return lotes_para_resgate

    def simular_cenario_resgate(
        self,
        lote_id: int,
        etapas: List[Dict[str, Any]],
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Simula um cenário de resgate com etapas hipotéticas.

        Args:
            lote_id: ID do lote a simular
            etapas: Lista de etapas com duração em dias
                Ex: [{'nome': 'Triagem', 'duracao_dias': 5}, {'nome': 'Aprovação', 'duracao_dias': 3}]
            seed: Seed para reprodutibilidade (opcional, usado para determinismo em validações)

        Returns:
            Dicionário com resultado da simulação
        """
        # Validar etapas
        if not etapas:
            raise ValueError("Pelo menos uma etapa deve ser informada")

        if len(etapas) > self.MAX_ETAPAS:
            raise ValueError(f"Máximo de {self.MAX_ETAPAS} etapas permitidas")

        total_duracao_dias = 0
        for etapa in etapas:
            duracao = etapa.get('duracao_dias', 0)
            if duracao < self.MIN_ETAPA_DIAS or duracao > self.MAX_ETAPA_DIAS:
                raise ValueError(f"Duração da etapa deve ser entre {self.MIN_ETAPA_DIAS} e {self.MAX_ETAPA_DIAS} dias")
            total_duracao_dias += duracao

        # Buscar lote
        lote = Medicamento.query.get(lote_id)
        if not lote:
            raise ValueError("Lote não encontrado")

        # Calcular dias para vencer
        dias_para_vencer = (lote.data_validade - date.today()).days

        # Calcular margem
        margem_dias = dias_para_vencer - total_duracao_dias

        # Determinar resultado
        if margem_dias < 0:
            resultado = "prazo_nao_compativel"
            mensagem = f"Praz não compatível com este cenário. Faltam {abs(margem_dias)} dias."
        elif margem_dias < 7:
            resultado = "margem_reduzida"
            mensagem = f"Margem reduzida ({margem_dias} dias). Recomenda revisar etapas."
        else:
            resultado = "compativel"
            mensagem = f"Compatível com as hipóteses informadas. Margem de {margem_dias} dias."

        return {
            'lote_id': lote_id,
            'nome': lote.nome,
            'lote': lote.lote,
            'data_validade': lote.data_validade.isoformat(),
            'dias_para_vencer': dias_para_vencer,
            'quantidade_cadastrada': lote.quantidade,
            'etapas': etapas,
            'total_duracao_dias': total_duracao_dias,
            'margem_dias': margem_dias,
            'resultado': resultado,
            'mensagem': mensagem,
            'simulado': True,
            'limitacoes': [
                "Saldo baseado em quantidade cadastrada (não derivado de ledger)",
                "Não há vínculo direto entre lote e farmácia",
                "Coordenadas da farmácia podem ser nulas (sem cálculo de distância)",
                "Leituras IoT não vinculadas a lotes (sem dados térmicos)",
                "Não há alteração de dados reais durante simulação"
            ]
        }

    def calcular_resumo_lotes(
        self,
        horizon_dias: int = 30,
        nome_medicamento: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calcula resumo de lotes para resgate.

        Args:
            horizon_dias: Horizonte em dias (1-365)
            nome_medicamento: Filtro opcional por nome

        Returns:
            Dicionário com resumo estatístico
        """
        lotes = self.listar_lotes_para_resgate(
            horizon_dias=horizon_dias,
            nome_medicamento=nome_medicamento
        )

        if not lotes:
            return {
                'total_lotes': 0,
                'total_quantidade': 0,
                'lotes_criticos': 0,
                'lotes_atencao': 0,
                'lotes_normais': 0,
                'horizonte_dias': horizon_dias
            }

        total_quantidade = sum(l['quantidade_cadastrada'] for l in lotes)
        lotes_criticos = sum(1 for l in lotes if l['dias_para_vencer'] <= 7)
        lotes_atencao = sum(1 for l in lotes if 7 < l['dias_para_vencer'] <= 30)
        lotes_normais = sum(1 for l in lotes if l['dias_para_vencer'] > 30)

        return {
            'total_lotes': len(lotes),
            'total_quantidade': total_quantidade,
            'lotes_criticos': lotes_criticos,
            'lotes_atencao': lotes_atencao,
            'lotes_normais': lotes_normais,
            'horizonte_dias': horizon_dias
        }
