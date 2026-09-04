from functools import wraps
from flask import abort, redirect, url_for, request, session
from flask_login import current_user
from datetime import datetime
import traceback


def _cargo_normalizado(cargo):
    mapa = {
        "admin": "Admin",
        "operador": "Operador",
        "receptor": "Operador",
        "voluntario": "Voluntário",
        "voluntário": "Voluntário",
        "medico": "Médico",
        "médico": "Médico",
        "farmaceutico": "Farmacêutico",
        "farmacêutico": "Farmacêutico",
        "doador": "Doador",
    }
    if not cargo:
        return ""
    chave = str(cargo).strip().lower()
    return mapa.get(chave, str(cargo).strip())


def cargo_permitido(cargo_usuario, cargos):
    cargo_atual = _cargo_normalizado(cargo_usuario)
    cargos_validos = {_cargo_normalizado(cargo) for cargo in cargos}
    return cargo_atual in cargos_validos


def cargo_required(*cargos):
    """Restringe acesso a usuários cujo cargo esteja na lista fornecida. Retorna 403 se negado."""

    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("auth.login"))
            if not cargo_permitido(current_user.cargo, cargos):
                abort(403)
            return f(*args, **kwargs)

        return decorated

    return decorator


def admin_required(f):
    """Acesso exclusivo para Administradores. Retorna 403 se negado."""

    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        if not cargo_permitido(current_user.cargo, ("Admin",)):
            abort(403)
        return f(*args, **kwargs)

    return decorated


def operador_required(f):
    """Acesso para Admin e Operador. Retorna 403 se negado."""

    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        if not cargo_permitido(current_user.cargo, ("Admin", "Operador")):
            abort(403)
        return f(*args, **kwargs)

    return decorated


def farmaceutico_required(f):
    """Acesso para Admin, Operador e Farmacêutico. Retorna 403 se negado."""

    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        if not cargo_permitido(
            current_user.cargo, ("Admin", "Operador", "Farmacêutico")
        ):
            abort(403)
        return f(*args, **kwargs)

    return decorated


def medico_required(f):
    """Acesso para Admin, Operador e Médico. Retorna 403 se negado."""

    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        if not cargo_permitido(current_user.cargo, ("Admin", "Operador", "Médico")):
            abort(403)
        return f(*args, **kwargs)

    return decorated


def equipe_clinica_required(f):
    """Acesso para Admin, Operador, Médico e Farmacêutico. Retorna 403 se negado."""

    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        if not cargo_permitido(
            current_user.cargo, ("Admin", "Operador", "Médico", "Farmacêutico")
        ):
            abort(403)
        return f(*args, **kwargs)

    return decorated


def log_audit_action(action_type, entity_type=None, entity_id=None, details=None):
    """
    Decorator para registrar ações críticas de auditoria automaticamente.
    Grava na tabela log_atividade informações sobre a ação do usuário.
    
    Uso:
        @log_audit_action('CADASTRO', 'DOACAO')
        def criar_doacao():
            ...
    
    Args:
        action_type: Tipo da ação (ex: 'CADASTRO', 'ALTERACAO', 'EXCLUSAO', 'LOGIN')
        entity_type: Tipo da entidade (ex: 'DOACAO', 'MEDICAMENTO', 'USUARIO')
        entity_id: ID da entidade (opcional, pode ser obtido do retorno da função)
        details: Detalhes adicionais da ação (opcional)
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Executa a função original
            result = f(*args, **kwargs)
            
            # Tenta registrar o log apenas se houver usuário autenticado
            try:
                from app.models.usuario import LogAtividade
                from app import db
                
                if current_user.is_authenticated:
                    # Obtém IP do usuário
                    ip_address = request.remote_addr or '127.0.0.1'
                    
                    # Obtém user agent
                    user_agent = request.headers.get('User-Agent', 'Unknown')[:200]
                    
                    # Constrói mensagem de ação
                    action_message = f"{action_type}"
                    if entity_type:
                        action_message += f" - {entity_type}"
                    if entity_id:
                        action_message += f" (ID: {entity_id})"
                    if details:
                        action_message += f" - {details}"
                    
                    # Cria registro de log
                    log_entry = LogAtividade(
                        usuario_id=current_user.id,
                        acao=action_message,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        data_hora=datetime.utcnow()
                    )
                    
                    db.session.add(log_entry)
                    db.session.commit()
                    
            except Exception as e:
                # Não interrompe a aplicação se o log falhar
                print(f"Erro ao registrar log de auditoria: {str(e)}")
                traceback.print_exc()
            
            return result
        return decorated
    return decorator


def log_login_attempt(success=True):
    """
    Decorator específico para registrar tentativas de login.
    Regra de negócio: registrar todas as tentativas, bem-sucedidas ou não.
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Executa a função original
            result = f(*args, **kwargs)
            
            try:
                from app.models.usuario import LogAtividade
                from app import db
                
                # Obtém CPF do formulário
                cpf = request.form.get('cpf', request.json.get('cpf', 'unknown'))
                
                # Obtém IP
                ip_address = request.remote_addr or '127.0.0.1'
                
                # Obtém user agent
                user_agent = request.headers.get('User-Agent', 'Unknown')[:200]
                
                # Determina status
                status = "LOGIN_SUCESSO" if success else "LOGIN_FALHA"
                
                # Cria registro de log
                log_entry = LogAtividade(
                    usuario_id=None,  # Será preenchido se login for bem-sucedido
                    acao=f"{status} - CPF: {cpf}",
                    ip_address=ip_address,
                    user_agent=user_agent,
                    data_hora=datetime.utcnow()
                )
                
                db.session.add(log_entry)
                db.session.commit()
                
            except Exception as e:
                print(f"Erro ao registrar log de login: {str(e)}")
                traceback.print_exc()
            
            return result
        return decorated
    return decorator
