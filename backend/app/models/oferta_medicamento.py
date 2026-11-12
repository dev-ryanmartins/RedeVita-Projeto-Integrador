from app.database import db
from datetime import datetime
from enum import Enum
from sqlalchemy import text


class StatusOferta(Enum):
    """Status da oferta de medicamento."""
    DISPONIVEL = "disponivel"
    RESERVADA = "reservada"
    APROVADA = "aprovada"
    CONFIRMADA = "confirmada"
    DESPACHADA = "despachada"
    CANCELADA = "cancelada"
    EXPIRADA = "expirada"


class OfertaMedicamento(db.Model):
    """
    Modelo para Oferta de Medicamento.
    
    Representa um medicamento disponível para doação antes da saída física.
    A reserva não reduz o estoque físico; a saída ocorre na etapa do fluxo logístico.
    """
    __tablename__ = "ofertas_medicamentos"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    
    # Farmácia doadora
    farmacia_id = db.Column(db.Integer, db.ForeignKey("farmacias.id"), nullable=False)
    
    # Medicamento e lote
    medicamento_id = db.Column(db.Integer, db.ForeignKey("medicamentos.id"), nullable=False)
    
    # Quantidade ofertada
    quantidade_ofertada = db.Column(db.Integer, nullable=False)
    
    # Quantidade reservada (controla disponibilidade)
    quantidade_reservada = db.Column(db.Integer, default=0, nullable=False)
    
    # Status da oferta
    status = db.Column(db.String(20), nullable=False, default=StatusOferta.DISPONIVEL.value)
    
    # Data de expiração da oferta (opcional)
    data_expiracao = db.Column(db.DateTime, nullable=True)
    
    # Responsável pela oferta
    criado_por_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    
    # Timestamps
    criado_em = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Observações
    observacoes = db.Column(db.Text, nullable=True)
    
    # Relacionamentos
    farmacia = db.relationship("Farmacia", foreign_keys=[farmacia_id], lazy=True)
    medicamento = db.relationship("Medicamento", foreign_keys=[medicamento_id], lazy=True)
    criado_por = db.relationship("Usuario", foreign_keys=[criado_por_id], overlaps='usuario')
    
    @property
    def quantidade_disponivel(self):
        """Quantidade disponível para reserva."""
        return self.quantidade_ofertada - self.quantidade_reservada
    
    def reservar(self, quantidade):
        """
        Reserva uma quantidade da oferta (não atômico - usar reservar_atomico para concorrência).
        
        Args:
            quantidade: Quantidade a reservar
            
        Returns:
            bool: True se a reserva foi bem-sucedida, False caso contrário
        """
        if quantidade <= 0:
            return False
        
        if self.quantidade_disponivel < quantidade:
            return False
        
        if self.status != StatusOferta.DISPONIVEL.value:
            return False
        
        self.quantidade_reservada += quantidade
        
        # Se toda a quantidade foi reservada, muda status para RESERVADA
        if self.quantidade_reservada >= self.quantidade_ofertada:
            self.status = StatusOferta.RESERVADA.value
        
        return True
    
    @classmethod
    def reservar_atomico(cls, session, oferta_id, quantidade):
        """
        Reserva uma quantidade da oferta de forma atômica usando UPDATE condicional.
        
        Este método usa um UPDATE condicional no banco para garantir atomicidade
        em cenários de concorrência. A operação só succeed se a quantidade a reservar
        não exceder a disponibilidade.
        
        Args:
            session: SQLAlchemy session
            oferta_id: ID da oferta
            quantidade: Quantidade a reservar
            
        Returns:
            tuple: (success: bool, nova_quantidade_reservada: int or None)
        """
        if quantidade <= 0:
            return (False, None)
        
        # UPDATE condicional: só atualiza se não exceder disponibilidade
        update_stmt = text("""
            UPDATE ofertas_medicamentos
            SET quantidade_reservada = quantidade_reservada + :quantidade,
                status = CASE 
                    WHEN quantidade_reservada + :quantidade >= quantidade_ofertada THEN :status_reservada
                    ELSE status
                END
            WHERE id = :oferta_id
              AND status = :status_disponivel
              AND quantidade_reservada + :quantidade <= quantidade_ofertada
        """)
        
        result = session.execute(
            update_stmt,
            {
                "quantidade": quantidade,
                "oferta_id": oferta_id,
                "status_disponivel": StatusOferta.DISPONIVEL.value,
                "status_reservada": StatusOferta.RESERVADA.value
            }
        )
        
        rowcount = result.rowcount
        
        if rowcount > 0:
            # Busca a nova quantidade reservada
            select_stmt = text("""
                SELECT quantidade_reservada FROM ofertas_medicamentos WHERE id = :oferta_id
            """)
            select_result = session.execute(select_stmt, {"oferta_id": oferta_id})
            row = select_result.fetchone()
            nova_quantidade = row[0] if row else None
            return (True, nova_quantidade)
        
        return (False, None)
    
    def liberar_reserva(self, quantidade):
        """
        Libera uma quantidade reservada (não atômico - usar liberar_reserva_atomico para idempotência).
        
        Args:
            quantidade: Quantidade a liberar
        """
        if quantidade <= 0:
            return
        
        self.quantidade_reservada = max(0, self.quantidade_reservada - quantidade)
    
    @classmethod
    def liberar_reserva_atomico(cls, session, oferta_id, quantidade):
        """
        Libera uma quantidade reservada de forma idempotente usando UPDATE condicional.
        
        Este método usa um UPDATE condicional para garantir que a liberação só ocorra
        se a quantidade reservada for suficiente, evitando liberações duplicadas.
        
        Args:
            session: SQLAlchemy session
            oferta_id: ID da oferta
            quantidade: Quantidade a liberar
            
        Returns:
            tuple: (success: bool, nova_quantidade_reservada: int or None)
        """
        if quantidade <= 0:
            return (False, None)
        
        # UPDATE condicional: só atualiza se houver quantidade suficiente reservada
        update_stmt = text("""
            UPDATE ofertas_medicamentos
            SET quantidade_reservada = GREATEST(0, quantidade_reservada - :quantidade)
            WHERE id = :oferta_id
              AND quantidade_reservada >= :quantidade
        """)
        
        result = session.execute(
            update_stmt,
            {
                "quantidade": quantidade,
                "oferta_id": oferta_id
            }
        )
        
        rowcount = result.rowcount
        
        if rowcount > 0:
            # Busca a nova quantidade reservada
            select_stmt = text("""
                SELECT quantidade_reservada FROM ofertas_medicamentos WHERE id = :oferta_id
            """)
            select_result = session.execute(select_stmt, {"oferta_id": oferta_id})
            row = select_result.fetchone()
            nova_quantidade = row[0] if row else None
            return (True, nova_quantidade)
        
        return (False, None)
    
    def confirmar(self):
        """Confirma a oferta (move para status CONFIRMADA)."""
        if self.status == StatusOferta.APROVADA.value:
            self.status = StatusOferta.CONFIRMADA.value
            return True
        return False
    
    def aprovar(self):
        """Aprova a oferta (move para status APROVADA)."""
        if self.status == StatusOferta.RESERVADA.value:
            self.status = StatusOferta.APROVADA.value
            return True
        return False
    
    def despachar(self):
        """Despacha a oferta (move para status DESPACHADA)."""
        if self.status == StatusOferta.CONFIRMADA.value:
            self.status = StatusOferta.DESPACHADA.value
            self.quantidade_reservada = 0
            return True
        return False
    
    def cancelar(self):
        """Cancela a oferta."""
        if self.status in [StatusOferta.DISPONIVEL.value, StatusOferta.RESERVADA.value]:
            self.status = StatusOferta.CANCELADA.value
            self.quantidade_reservada = 0
            return True
        return False
    
    def expirar(self):
        """Expira a oferta."""
        if self.status == StatusOferta.DISPONIVEL.value:
            self.status = StatusOferta.EXPIRADA.value
            self.quantidade_reservada = 0
            return True
        return False
    
    def __repr__(self):
        return f"<OfertaMedicamento {self.medicamento.nome if self.medicamento else 'N/A'} - {self.quantidade_ofertada}>"
