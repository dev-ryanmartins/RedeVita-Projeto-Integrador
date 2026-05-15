import os
from datetime import date
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.core.decorators import admin_required
from app.utils.notificacoes import (
    medicamentos_criticos, enviar_sms, enviar_whatsapp,
    enviar_email_alertas, contagem_alertas,
    medicamentos_vencidos_com_estoque, medicamentos_estoque_baixo,
)
from app.utils.log_helper import registrar_log

notificacoes_bp = Blueprint('notificacoes', __name__)


@notificacoes_bp.route('/notificacoes')
@login_required
@admin_required
def painel():
    twilio_ok = bool(
        os.environ.get('TWILIO_ACCOUNT_SID') and
        os.environ.get('TWILIO_AUTH_TOKEN') and
        os.environ.get('TWILIO_FROM_NUMBER')
    )
    mail_ok = bool(
        os.environ.get('MAIL_USERNAME') and
        os.environ.get('MAIL_PASSWORD')
    )
    meds_30     = medicamentos_criticos(30)
    meds_60     = medicamentos_criticos(60)
    meds_venc   = medicamentos_vencidos_com_estoque()
    meds_baixo  = medicamentos_estoque_baixo(10)
    hoje = date.today()
    return render_template(
        'notificacoes.html',
        twilio_ok=twilio_ok,
        mail_ok=mail_ok,
        meds_30=meds_30,
        meds_60=meds_60,
        meds_venc=meds_venc,
        meds_baixo=meds_baixo,
        hoje=hoje,
    )


@notificacoes_bp.route('/api/alertas')
@login_required
def api_alertas():
    """Endpoint JSON para o badge de alertas no menu."""
    return jsonify(contagem_alertas())


@notificacoes_bp.route('/notificacoes/enviar', methods=['POST'])
@login_required
@admin_required
def enviar():
    canal = request.form.get('canal', 'sms')
    dias_str = request.form.get('dias', '30')

    try:
        dias = int(dias_str)
    except ValueError:
        dias = 30

    if canal == 'email':
        destinatario = request.form.get('email_destino', '').strip()
        if not destinatario:
            flash('Informe um endereço de e-mail.', 'danger')
            return redirect(url_for('notificacoes.painel'))
        resultado = enviar_email_alertas(destinatario, dias)
        if resultado['ok']:
            if resultado.get('enviado'):
                registrar_log('Alerta por E-mail', f'E-mail enviado para {destinatario} — {resultado["mensagem"]}')
                flash(resultado['mensagem'], 'success')
            else:
                flash(resultado['mensagem'], 'info')
        else:
            flash(resultado['mensagem'], 'danger')
        return redirect(url_for('notificacoes.painel'))

    telefone = request.form.get('telefone', '').strip()
    if not telefone:
        flash('Informe um número de telefone.', 'danger')
        return redirect(url_for('notificacoes.painel'))

    telefone_limpo = '+' + ''.join(c for c in telefone if c.isdigit() or c == '+')
    if not telefone_limpo.startswith('+'):
        telefone_limpo = '+55' + telefone_limpo.lstrip('+')

    if canal == 'whatsapp':
        resultado = enviar_whatsapp(telefone_limpo, dias)
    else:
        resultado = enviar_sms(telefone_limpo, dias)

    if resultado['ok']:
        if resultado.get('enviado'):
            registrar_log('Notificação Enviada', f'{canal.upper()} enviado para {telefone_limpo} — {resultado["mensagem"]}')
            flash(resultado['mensagem'], 'success')
        else:
            flash(resultado['mensagem'], 'info')
    else:
        flash(resultado['mensagem'], 'danger')

    return redirect(url_for('notificacoes.painel'))
