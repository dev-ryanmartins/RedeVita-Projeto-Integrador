"""
QR Nonce Model for secure, single-use prescription dispensation.

This model stores opaque tokens used in QR codes for prescription dispensation.
The QR code contains only the nonce (token), while the server maintains the
link to the prescription, expiration, and usage status.
"""

import secrets
from datetime import datetime, timedelta
from app.database import db


class QRNonce(db.Model):
    """
    QR Nonce for secure prescription dispensation.
    
    Stores an opaque token that can be used once to dispense a prescription.
    The token is randomly generated and does not contain personal or clinical data.
    """
    __tablename__ = "qr_nonces"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    nonce = db.Column(db.String(64), unique=True, nullable=False, index=True)
    receita_id = db.Column(db.Integer, db.ForeignKey("receitas.id"), nullable=False, index=True)
    gerado_por_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    
    # Expiration time - configurable, defaults to 15 minutes
    expira_em = db.Column(db.DateTime, nullable=False)
    
    # Usage tracking
    usado = db.Column(db.Boolean, default=False, nullable=False)
    usado_em = db.Column(db.DateTime, nullable=True)
    usado_por_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    
    # Timestamps
    criado_em = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    receita = db.relationship("Receita", backref="qr_nonces", lazy=True)
    gerado_por = db.relationship("Usuario", foreign_keys=[gerado_por_id], lazy=True)
    usado_por = db.relationship("Usuario", foreign_keys=[usado_por_id], lazy=True)

    @staticmethod
    def generate_nonce(length=32):
        """
        Generate a cryptographically secure random nonce.
        
        Args:
            length: Length of the nonce in bytes (default 32 = 256 bits)
        
        Returns:
            Hexadecimal string representation of the random bytes.
        """
        return secrets.token_hex(length)

    @classmethod
    def create_for_prescription(cls, receita_id, gerado_por_id=None, expiracao_minutos=15):
        """
        Create a new QR nonce for a prescription.
        
        Args:
            receita_id: ID of the prescription.
            gerado_por_id: ID of the user who generated the nonce (optional).
            expiracao_minutos: Expiration time in minutes (default 15).
        
        Returns:
            QRNonce instance.
        """
        nonce = cls.generate_nonce()
        expira_em = datetime.utcnow() + timedelta(minutes=expiracao_minutos)
        
        qr_nonce = cls(
            nonce=nonce,
            receita_id=receita_id,
            gerado_por_id=gerado_por_id,
            expira_em=expira_em
        )
        
        db.session.add(qr_nonce)
        db.session.commit()
        
        return qr_nonce

    def is_valid(self):
        """
        Check if the nonce is valid (not expired and not used).
        
        Returns:
            True if valid, False otherwise.
        """
        if self.usado:
            return False
        
        if datetime.utcnow() > self.expira_em:
            return False
        
        return True

    def mark_as_used(self, usado_por_id):
        """
        Mark the nonce as used.
        
        Args:
            usado_por_id: ID of the user who used the nonce.
        """
        self.usado = True
        self.usado_em = datetime.utcnow()
        self.usado_por_id = usado_por_id
        db.session.commit()

    def __repr__(self):
        return f"<QRNonce {self.nonce[:8]}... (receita_id={self.receita_id})>"
