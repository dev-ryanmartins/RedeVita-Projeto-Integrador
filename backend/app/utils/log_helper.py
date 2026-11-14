from flask import request
from flask_login import current_user
from functools import wraps
from datetime import datetime


def registrar_log(acao: str, detalhes: str = None):
    """Registra uma ação de auditoria no banco de dados."""
    try:
        from app.models.log_atividade import LogAtividade
        from app.database import db

        usuario_id = (
            current_user.id if current_user and current_user.is_authenticated else None
        )
        ip = request.remote_addr or "desconhecido"

        log = LogAtividade(usuario_id=usuario_id, acao=acao, detalhes=detalhes, ip=ip)
        db.session.add(log)
        db.session.commit()
    except Exception:
        pass


def audit_action(action_type: str):
    """
    Decorator para registrar automaticamente ações de auditoria críticas.
    Grava usuário, rota, IP e timestamp na tabela log_atividade.

    Uso:
        @audit_action("Criação de Medicamento")
        def criar_medicamento():
            # lógica da função
            pass
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            # Executa a função original
            result = f(*args, **kwargs)

            # Registra a ação de auditoria após execução bem-sucedida
            try:
                from app.models.log_atividade import LogAtividade
                from app.database import db

                usuario_id = (
                    current_user.id if current_user and current_user.is_authenticated else None
                )
                ip = request.remote_addr or "desconhecido"
                rota = request.endpoint or request.path or "desconhecida"
                metodo = request.method or "GET"

                # Detalhes da ação
                detalhes = f"{metodo} {rota}"
                if hasattr(request, 'json') and request.json:
                    detalhes += f" | Payload: {str(request.json)[:200]}"

                log = LogAtividade(
                    usuario_id=usuario_id,
                    acao=action_type,
                    detalhes=detalhes,
                    ip=ip,
                    timestamp=datetime.utcnow()
                )
                db.session.add(log)
                db.session.commit()
            except Exception:
                # Não falha a função original se o log falhar
                pass

            return result
        return wrapped
    return decorator
