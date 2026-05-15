from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.database import db
from app.core.security import criptografar_senha, verificar_senha
from app.utils.log_helper import registrar_log

perfil_bp = Blueprint('perfil', __name__)


@perfil_bp.route('/perfil', methods=['GET', 'POST'])
@login_required
def meu_perfil():
    if request.method == 'POST':
        action = request.form.get('action', '')

        if action == 'perfil':
            nome = request.form.get('nome', '').strip()
            email = request.form.get('email', '').strip() or None
            if not nome:
                flash('O nome é obrigatório.', 'danger')
                return redirect(url_for('perfil.meu_perfil'))
            current_user.nome = nome
            current_user.email = email
            db.session.commit()
            registrar_log('Perfil Atualizado', 'Usuário atualizou dados do perfil')
            flash('Perfil atualizado com sucesso!', 'success')

        elif action == 'senha':
            senha_atual = request.form.get('senha_atual', '')
            nova_senha = request.form.get('nova_senha', '')
            confirmar = request.form.get('confirmar_senha', '')
            if not verificar_senha(current_user.senha, senha_atual):
                flash('Senha atual incorreta.', 'danger')
                return redirect(url_for('perfil.meu_perfil'))
            if len(nova_senha) < 6:
                flash('A nova senha deve ter pelo menos 6 caracteres.', 'danger')
                return redirect(url_for('perfil.meu_perfil'))
            if nova_senha != confirmar:
                flash('A confirmação de senha não confere.', 'danger')
                return redirect(url_for('perfil.meu_perfil'))
            current_user.senha = criptografar_senha(nova_senha)
            db.session.commit()
            registrar_log('Senha Alterada', 'Usuário alterou sua própria senha')
            flash('Senha alterada com sucesso!', 'success')

        return redirect(url_for('perfil.meu_perfil'))

    return render_template('perfil.html')
