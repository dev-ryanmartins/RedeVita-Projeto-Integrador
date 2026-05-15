from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user


def cargo_required(*cargos):
    """Restringe acesso a usuários cujo cargo esteja na lista fornecida. Retorna 403 se negado."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            if current_user.cargo not in cargos:
                abort(403)
            return f(*args, **kwargs)
        return decorated
    return decorator


def admin_required(f):
    """Acesso exclusivo para Administradores. Retorna 403 se negado."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.cargo != 'Admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated


def operador_required(f):
    """Acesso para Admin e Operador. Retorna 403 se negado."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.cargo not in ('Admin', 'Operador'):
            abort(403)
        return f(*args, **kwargs)
    return decorated


def farmaceutico_required(f):
    """Acesso para Admin, Operador e Farmacêutico. Retorna 403 se negado."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.cargo not in ('Admin', 'Operador', 'Farmacêutico'):
            abort(403)
        return f(*args, **kwargs)
    return decorated


def medico_required(f):
    """Acesso para Admin, Operador e Médico. Retorna 403 se negado."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.cargo not in ('Admin', 'Operador', 'Médico'):
            abort(403)
        return f(*args, **kwargs)
    return decorated


def equipe_clinica_required(f):
    """Acesso para Admin, Operador, Médico e Farmacêutico. Retorna 403 se negado."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.cargo not in ('Admin', 'Operador', 'Médico', 'Farmacêutico'):
            abort(403)
        return f(*args, **kwargs)
    return decorated
