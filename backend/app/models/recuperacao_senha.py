from app.database import db
from datetime import datetime, timedelta
import secrets


class RecuperacaoSenha(db.Model):
    """Modelo para tokens de recuperação de senha armazenados no servidor."""
    __tablename__ = "recuperacoes_senha"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False, index=True)
    
    # Token seguro e aleatório (32 bytes = 256 bits)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    
    # Hash do token para validação segura (mesmo que armazenar token, hash para comparação)
    token_hash = db.Column(db.String(64), nullable=False, index=True)
    
    # Expiração (padrão: 15 minutos)
    expira_em = db.Column(db.DateTime, nullable=False, index=True)
    
    # Controle de uso único
    usado_em = db.Column(db.DateTime, nullable=True)
    
    # Limite de tentativas
    tentativas = db.Column(db.Integer, default=0, nullable=False)
    max_tentativas = db.Column(db.Integer, default=5, nullable=False)
    
    # Timestamps
    criado_em = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # IP de origem para auditoria
    ip_origem = db.Column(db.String(45), nullable=True)
    
    # Relacionamentos
    usuario = db.relationship("Usuario", backref="recuperacoes_senha")

    @staticmethod
    def gerar_token_seguro(length=32):
        """Gera um token criptograficamente seguro."""
        return secrets.token_urlsafe(length)

    @classmethod
    def criar_token(cls, usuario_id, ip_origem=None, expiracao_minutos=15, max_tentativas=5):
        """Cria um novo token de recuperação para o usuário."""
        token = cls.gerar_token_seguro()
        token_hash = secrets.token_urlsafe(32)
        expira_em = datetime.utcnow() + timedelta(minutes=expiracao_minutos)
        
        recuperacao = cls(
            usuario_id=usuario_id,
            token=token,
            token_hash=token_hash,
            expira_em=expira_em,
            max_tentativas=max_tentativas,
            ip_origem=ip_origem
        )
        
        db.session.add(recuperacao)
        db.session.commit()
        
        return recuperacao

    def is_valido(self):
        """Verifica se o token ainda é válido (não usado, não expirado, dentro do limite de tentativas)."""
        if self.usado_em is not None:
            return False
        if datetime.utcnow() > self.expira_em:
            return False
        if self.tentativas >= self.max_tentativas:
            return False
        return True

    def registrar_tentativa(self):
        """Registra uma tentativa de uso do token."""
        self.tentativas += 1
        db.session.commit()

    def marcar_como_usado(self):
        """Marca o token como usado (uso único)."""
        self.usado_em = datetime.utcnow()
        db.session.commit()

    def __repr__(self):
        return f"<RecuperacaoSenha usuario_id={self.usuario_id} token={self.token[:8]}...>"
