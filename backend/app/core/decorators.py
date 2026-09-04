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
    """
    Acesso para Admin e Operador.
    Responsabilidades: Cadastro e conferência de entradas de doações e triagem inicial de validade.
    Retorna 403 se negado.
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        if not cargo_permitido(current_user.cargo, ("Admin", "Operador")):
            abort(403)
        return f(*args, **kwargs)

    return decorated


def farmaceutico_required(f):
    """
    Acesso exclusivo para Farmacêutico e Admin.
    Conforme Portaria 344/ANVISA - controle de medicamentos refrigerados/controlados.
    Retorna 403 se negado.
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        if not cargo_permitido(current_user.cargo, ("Admin", "Farmacêutico")):
            abort(403)
        return f(*args, **kwargs)

    return decorated


def medico_required(f):
    """
    Acesso exclusivo para Médico e Admin.
    Conforme especificações do sistema - gestão de pacientes e receituário.
    Retorna 403 se negado.
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        if not cargo_permitido(current_user.cargo, ("Admin", "Médico")):
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


def voluntario_required(f):
    """
    Acesso para todos os usuários autenticados (Admin, Operador, Farmacêutico, Médico, Voluntário).
    Responsabilidades do Voluntário: Auxílio no recebimento e registro de doações comunitárias.
    Retorna 403 se negado.
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
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


def farmacia_vinculada_required(f):
    """
    Decorator para validar que uma farmácia está vinculada ao contexto.
    Garante conformidade com Portaria 344/ANVISA para controle de refrigerados.
    
    Verifica:
    1. Usuário autenticado
    2. Permissão de Farmacêutico ou Admin
    3. Farmácia está selecionada/indicada nos parâmetros
    
    Retorna 403 se negado ou erro informando que farmácia deve ser selecionada.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Verifica autenticação
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        
        # Verifica permissão (apenas Farmacêutico e Admin)
        if not cargo_permitido(current_user.cargo, ("Admin", "Farmacêutico")):
            abort(403)
        
        # Verifica se há farmácia nos parâmetros ou no contexto
        farmacia_id = request.args.get('farmacia_id') or request.json.get('farmacia_id') if request.is_json else None
        
        if not farmacia_id:
            # Verifica se há farmácia padrão para o usuário
            from app.models.farmacia import Farmacia
            from app.database import db
            
            try:
                # Tenta encontrar farmácia vinculada ao usuário (se houver relação)
                # Se não houver, exige que o usuário selecione uma farmácia
                total_farmacias = Farmacia.query.count()
                if total_farmacias == 0:
                    from flask import jsonify
                    return jsonify({
                        'error': 'Nenhuma farmácia cadastrada',
                        'message': 'Cadastre uma farmácia parceira antes de acessar o painel de controle',
                        'action': 'cadastrar_farmacia'
                    }), 400
            except Exception:
                pass
            
            # Se não especificar farmácia, mas houver farmácias cadastradas, retorna erro
            from flask import jsonify
            return jsonify({
                'error': 'Farmácia não selecionada',
                'message': 'Selecione uma farmácia parceira para continuar',
                'action': 'selecionar_farmacia'
            }), 400
        
        # Valida se a farmácia existe
        try:
            from app.models.farmacia import Farmacia
            from app.database import db
            
            farmacia = Farmacia.query.get(farmacia_id)
            if not farmacia:
                from flask import jsonify
                return jsonify({
                    'error': 'Farmácia não encontrada',
                    'message': 'A farmácia selecionada não existe no sistema'
                }), 404
        except Exception as e:
            from flask import jsonify
            return jsonify({
                'error': 'Erro ao validar farmácia',
                'message': str(e)
            }), 500
        
        # Adiciona farmacia_id ao kwargs para a função usar
        kwargs['farmacia_id'] = farmacia_id
        
        return f(*args, **kwargs)
    
    return decorated
