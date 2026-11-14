from app.database import db
from datetime import datetime


class ReceitaAnexo(db.Model):
    """
    Modelo para Anexo de Receita Digitalizada.
    
    Vinculado a uma reserva de oferta, armazena a receita digitalizada
    exigida para medicamentos controlados.
    """
    __tablename__ = "receitas_anexos"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    
    # Reserva vinculada (uma receita por reserva)
    reserva_id = db.Column(db.Integer, db.ForeignKey("reservas_ofertas.id"), nullable=False, unique=True)
    
    # Metadados do arquivo
    nome_arquivo_original = db.Column(db.String(255), nullable=False)
    nome_arquivo_interno = db.Column(db.String(255), nullable=False, unique=True)
    caminho_arquivo = db.Column(db.String(512), nullable=False)
    tamanho_bytes = db.Column(db.Integer, nullable=False)
    tipo_mime = db.Column(db.String(100), nullable=False)
    
    # Controle de validação
    validado = db.Column(db.Boolean, default=False, nullable=False)
    
    # Responsável pelo upload
    uploadado_por_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    uploadado_em = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Observações
    observacoes = db.Column(db.Text, nullable=True)
    
    # Relacionamentos
    reserva = db.relationship("ReservaOferta", foreign_keys=[reserva_id], lazy=True)
    uploadado_por = db.relationship("Usuario", foreign_keys=[uploadado_por_id], overlaps='usuario')
    
    def __repr__(self):
        return f"<ReceitaAnexo {self.id} - Reserva {self.reserva_id}>"
