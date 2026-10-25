from app.database import db
from datetime import datetime
import secrets


class QRNonce(db.Model):
    """Modelo para nonces de QR Code de uso único."""
    __tablename__ = "qr_nonces"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    nonce = db.Column(db.String(64), unique=True, nullable=False, index=True)
    tipo = db.Column(db.String(50), nullable=False)
    receita_id = db.Column(db.Integer, db.ForeignKey("receitas.id"), nullable=True)
    medicamento_id = db.Column(db.Integer, db.ForeignKey("medicamentos.id"), nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expira_em = db.Column(db.DateTime, nullable=False)
    usado_em = db.Column(db.DateTime, nullable=True)
    usado = db.Column(db.Boolean, default=False, nullable=False)
    usado_por_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)

    @staticmethod
    def gerar_nonce():
        return secrets.token_urlsafe(48)

    @staticmethod
    def criar_nonce(tipo: str, receita_id: int = None, medicamento_id: int = None, validade_segundos: int = 900):
        nonce_str = QRNonce.gerar_nonce()
        expira_em = datetime.utcnow() + timedelta(seconds=validade_segundos)
        qr_nonce = QRNonce(nonce=nonce_str, tipo=tipo, receita_id=receita_id, medicamento_id=medicamento_id, expira_em=expira_em)
        db.session.add(qr_nonce)
        db.session.commit()
        return qr_nonce

    def validar_uso(self):
        if self.usado:
            return False
        if datetime.utcnow() > self.expira_em:
            return False
        return True

    def marcar_como_usado(self, usuario_id: int):
        self.usado = True
        self.usado_em = datetime.utcnow()
        self.usado_por_id = usuario_id
        db.session.commit()
