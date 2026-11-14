"""
Serviço de Matching entre Ofertas e Necessidades Institucionais

Corresponde ofertas de medicamentos disponíveis com necessidades de instituições.
Considera compatibilidade de medicamento, quantidade e validade.
Não sugere equivalência terapêutica, substituição ou prioridade artificial.
"""

from app.models.oferta_medicamento import OfertaMedicamento, StatusOferta
from app.models.necessidade_institucional import NecessidadeInstitucional, StatusNecessidade
from app.models.medicamento import Medicamento
from app.models.medicamento_referencia import MedicamentoReferencia
from app.database import db
from datetime import datetime


class MatchResultado:
    """Resultado de um match entre oferta e necessidade."""
    
    def __init__(self, oferta, necessidade, compativel, motivo=""):
        self.oferta = oferta
        self.necessidade = necessidade
        self.compativel = compativel
        self.motivo = motivo


class MatchingService:
    """Serviço para matching de ofertas e necessidades."""
    
    @staticmethod
    def buscar_matches_para_necessidade(necessidade_id, limite=10):
        """
        Busca ofertas compatíveis para uma necessidade específica.
        
        Args:
            necessidade_id: ID da necessidade institucional
            limite: Número máximo de matches a retornar
            
        Returns:
            list: Lista de MatchResultado
        """
        necessidade = db.session.get(NecessidadeInstitucional, necessidade_id)
        if not necessidade:
            return []
        
        # Busca ofertas disponíveis (filtrando ofertas inadequadas)
        hoje = datetime.now().date()
        ofertas = OfertaMedicamento.query.filter(
            OfertaMedicamento.status == StatusOferta.DISPONIVEL.value
        ).all()
        
        matches = []
        for oferta in ofertas:
            # Filtra ofertas inadequadas
            if not MatchingService._oferta_adequada(oferta, hoje):
                continue
            
            resultado = MatchingService._calcular_match(oferta, necessidade)
            if resultado.compativel:
                matches.append(resultado)
        
        return matches[:limite]
    
    @staticmethod
    def buscar_matches_para_oferta(oferta_id, limite=10):
        """
        Busca necessidades compatíveis para uma oferta específica.
        
        Args:
            oferta_id: ID da oferta de medicamento
            limite: Número máximo de matches a retornar
            
        Returns:
            list: Lista de MatchResultado
        """
        oferta = db.session.get(OfertaMedicamento, oferta_id)
        if not oferta:
            return []
        
        # Filtra ofertas inadequadas
        hoje = datetime.now().date()
        if not MatchingService._oferta_adequada(oferta, hoje):
            return []
        
        # Busca necessidades registradas ou em revisão
        necessidades = NecessidadeInstitucional.query.filter(
            NecessidadeInstitucional.status.in_([
                StatusNecessidade.REGISTRADA.value,
                StatusNecessidade.EM_REVISAO.value
            ])
        ).all()
        
        matches = []
        for necessidade in necessidades:
            resultado = MatchingService._calcular_match(oferta, necessidade)
            if resultado.compativel:
                matches.append(resultado)
        
        return matches[:limite]
    
    @staticmethod
    def _oferta_adequada(oferta, data_hoje):
        """
        Verifica se uma oferta é adequada para matching.
        
        Filtra ofertas vencidas, bloqueadas, indisponíveis ou totalmente reservadas.
        
        Args:
            oferta: OfertaMedicamento
            data_hoje: Data atual para verificar validade
            
        Returns:
            bool: True se oferta é adequada, False caso contrário
        """
        # Verifica se está disponível
        if oferta.status != StatusOferta.DISPONIVEL.value:
            return False
        
        # Verifica se tem quantidade disponível
        if oferta.quantidade_disponivel <= 0:
            return False
        
        # Verifica se não está vencida
        if oferta.medicamento and oferta.medicamento.data_validade:
            if oferta.medicamento.data_validade < data_hoje:
                return False
        
        return True
    
    @staticmethod
    def _calcular_match(oferta, necessidade):
        """
        Calcula a compatibilidade entre oferta e necessidade.
        
        Matching puramente informativo: não sugere equivalência terapêutica,
        substituição ou prioridade artificial.
        
        Args:
            oferta: OfertaMedicamento
            necessidade: NecessidadeInstitucional
            
        Returns:
            MatchResultado: Resultado do match com compatibilidade e motivo
        """
        motivos = []
        
        # Verifica se há quantidade disponível suficiente
        if oferta.quantidade_disponivel < necessidade.quantidade_solicitada:
            return MatchResultado(oferta, necessidade, False, "Quantidade insuficiente")
        
        motivos.append("Quantidade suficiente")
        
        # Verifica compatibilidade de medicamento
        if oferta.medicamento:
            if necessidade.medicamento_referencia_id:
                # Se a necessidade tem referência, verifica se o medicamento corresponde
                if oferta.medicamento.referencia_id == necessidade.medicamento_referencia_id:
                    motivos.append("Medicamento exato")
                else:
                    # Não sugere equivalência terapêutica
                    return MatchResultado(oferta, necessidade, False, "Medicamento diferente")
            else:
                # Se a necessidade não tem referência, verifica nome descritivo
                if necessidade.produto_descritivo:
                    nome_oferta = oferta.medicamento.nome.lower()
                    nome_necessidade = necessidade.produto_descritivo.lower()
                    if nome_oferta in nome_necessidade or nome_necessidade in nome_oferta:
                        motivos.append("Nome compatível")
                    else:
                        return MatchResultado(oferta, necessidade, False, "Nome incompatível")
        
        # Verifica validade (não expirado)
        if oferta.medicamento and oferta.medicamento.data_validade:
            data_validade_dt = datetime.combine(oferta.medicamento.data_validade, datetime.min.time())
            dias_para_validade = (data_validade_dt - datetime.utcnow()).days
            if dias_para_validade < 30:
                return MatchResultado(oferta, necessidade, False, "Validade curta (menos de 30 dias)")
            motivos.append(f"Validade: {dias_para_validade} dias")
        
        motivo_str = ", ".join(motivos) if motivos else "Compatível"
        
        return MatchResultado(oferta, necessidade, True, motivo_str)
    
    @staticmethod
    def sugerir_reserva(oferta_id, necessidade_id):
        """
        Sugere a criação de uma reserva entre oferta e necessidade.
        
        Args:
            oferta_id: ID da oferta
            necessidade_id: ID da necessidade
            
        Returns:
            dict: Informações sobre a sugestão (compatível, quantidade, etc.)
        """
        oferta = db.session.get(OfertaMedicamento, oferta_id)
        necessidade = db.session.get(NecessidadeInstitucional, necessidade_id)
        
        if not oferta or not necessidade:
            return {"compativel": False, "motivo": "Oferta ou necessidade não encontrada"}
        
        if oferta.status != StatusOferta.DISPONIVEL.value:
            return {"compativel": False, "motivo": "Oferta não está disponível"}
        
        if necessidade.status not in [StatusNecessidade.REGISTRADA.value, StatusNecessidade.EM_REVISAO.value]:
            return {"compativel": False, "motivo": "Necessidade não está ativa"}
        
        resultado = MatchingService._calcular_match(oferta, necessidade)
        
        if not resultado.compativel:
            return {"compativel": False, "motivo": resultado.motivo}
        
        # Determina quantidade a reservar
        quantidade_reservar = min(oferta.quantidade_disponivel, necessidade.quantidade_solicitada)
        
        return {
            "compativel": True,
            "motivo": resultado.motivo,
            "quantidade_disponivel": oferta.quantidade_disponivel,
            "quantidade_solicitada": necessidade.quantidade_solicitada,
            "quantidade_sugerida": quantidade_reservar,
            "oferta": {
                "id": oferta.id,
                "medicamento": oferta.medicamento.nome if oferta.medicamento else "N/A",
                "farmacia": oferta.farmacia.nome_fantasia if oferta.farmacia else "N/A"
            },
            "necessidade": {
                "id": necessidade.id,
                "instituicao": necessidade.instituicao.nome if necessidade.instituicao else necessidade.nome_instituicao,
                "produto": necessidade.produto_descritivo or "N/A"
            }
        }
