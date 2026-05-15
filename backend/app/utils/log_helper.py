from flask import request
from flask_login import current_user


def registrar_log(acao: str, detalhes: str = None):
    """Registra uma ação de auditoria no banco de dados."""
    try:
        from app.models.log_atividade import LogAtividade
        from app.database import db

        usuario_id = current_user.id if current_user and current_user.is_authenticated else None
        ip = request.remote_addr or 'desconhecido'

        log = LogAtividade(
            usuario_id=usuario_id,
            acao=acao,
            detalhes=detalhes,
            ip=ip
        )
        db.session.add(log)
        db.session.commit()
    except Exception:
        pass
