from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.doacao import Doacao
from app.models.medicamento import Medicamento
from app.database import db
from app.utils.log_helper import registrar_log
from app.core.decorators import cargo_required, admin_required
from app.utils.semaforo import calcular_status_semaforo
from datetime import datetime

donation_bp = Blueprint('donation', __name__)

TARJAS_VALIDAS = ['Sem Tarja', 'Tarja Amarela', 'Tarja Vermelha', 'Portaria 344']


# ── Doações (saída de medicamentos) ──────────────────────────────────────────

@donation_bp.route('/doacoes', methods=['GET', 'POST'])
@login_required
def nova_doacao():
    if request.method == 'POST':
        med_id = request.form.get('medicamento_id')
        quantidade_str = request.form.get('quantidade', '0')
        destinatario = request.form.get('destinatario', '').strip() or 'Não informado'
        observacao = request.form.get('observacao', '').strip() or None

        try:
            qtd = int(quantidade_str)
            if qtd <= 0:
                flash('A quantidade deve ser maior que zero.', 'danger')
                return redirect(url_for('donation.nova_doacao'))
        except ValueError:
            flash('Quantidade inválida.', 'danger')
            return redirect(url_for('donation.nova_doacao'))

        medicamento = db.session.get(Medicamento, med_id)

        if not medicamento:
            flash('Medicamento não encontrado.', 'danger')
            return redirect(url_for('donation.nova_doacao'))

        if medicamento.quantidade < qtd:
            flash('Quantidade insuficiente no estoque.', 'danger')
            return redirect(url_for('donation.nova_doacao'))

        try:
            medicamento.quantidade -= qtd
            registro = Doacao(
                usuario_id=current_user.id,
                medicamento_id=medicamento.id,
                quantidade=qtd
            )
            db.session.add(registro)
            db.session.commit()
            detalhe = (
                f'{qtd} un. de "{medicamento.nome}" (Lote {medicamento.lote}) '
                f'por {current_user.nome} [{current_user.cargo}] → {destinatario}'
            )
            if observacao:
                detalhe += f' | Obs: {observacao}'
            registrar_log('Doação Registrada', detalhe)
            flash('Doação registrada com sucesso!', 'success')
        except Exception:
            db.session.rollback()
            flash('Erro ao registrar doação. Tente novamente.', 'danger')

        return redirect(url_for('donation.nova_doacao'))

    medicamentos = Medicamento.query.filter(Medicamento.quantidade > 0).all()

    data_inicio = request.args.get('data_inicio', '').strip()
    data_fim = request.args.get('data_fim', '').strip()
    q = Doacao.query.order_by(Doacao.data_doacao.desc())
    if data_inicio:
        try:
            q = q.filter(Doacao.data_doacao >= datetime.strptime(data_inicio, '%Y-%m-%d'))
        except ValueError:
            pass
    if data_fim:
        try:
            q = q.filter(Doacao.data_doacao <= datetime.strptime(data_fim + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))
        except ValueError:
            pass
    doacoes = q.all()

    return render_template(
        'doacoes.html',
        medicamentos=medicamentos,
        doacoes=doacoes,
        data_inicio=data_inicio,
        data_fim=data_fim,
    )


# ── Triagem de entrada (recebimento de medicamentos doados ao estoque) ────────

@donation_bp.route('/doacoes/triagem', methods=['GET', 'POST'])
@login_required
@cargo_required('Admin', 'Operador', 'Farmacêutico')
def triagem():
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        lote = request.form.get('lote', '').strip()
        data_validade_str = request.form.get('data_validade', '').strip()
        quantidade_str = request.form.get('quantidade', '0').strip()
        tarja = request.form.get('tarja', 'Sem Tarja').strip()
        principio_ativo = request.form.get('principio_ativo', '').strip() or None
        doador = request.form.get('doador', '').strip() or 'Não informado'
        observacoes = request.form.get('observacoes', '').strip() or None

        if not nome or not lote or not data_validade_str or not quantidade_str:
            flash('Preencha todos os campos obrigatórios.', 'danger')
            return redirect(url_for('donation.triagem'))

        try:
            quantidade = int(quantidade_str)
            if quantidade <= 0:
                raise ValueError
        except ValueError:
            flash('Quantidade inválida. Informe um número inteiro positivo.', 'danger')
            return redirect(url_for('donation.triagem'))

        try:
            data_validade = datetime.strptime(data_validade_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Data de validade inválida.', 'danger')
            return redirect(url_for('donation.triagem'))

        if tarja not in TARJAS_VALIDAS:
            tarja = 'Sem Tarja'

        try:
            status = calcular_status_semaforo(data_validade)
            med = Medicamento(
                nome=nome,
                lote=lote,
                data_validade=data_validade,
                quantidade=quantidade,
                status_semaforo=status,
                tarja=tarja,
                principio_ativo=principio_ativo,
            )
            db.session.add(med)
            db.session.commit()
            registrar_log(
                'Triagem — Entrada de Medicamento',
                f'"{nome}" (Lote {lote}, {quantidade} un.) recebido de "{doador}" e adicionado ao estoque'
                + (f' | Obs: {observacoes}' if observacoes else '')
            )
            if status == 2:
                flash(f'⚠ "{nome}" adicionado, mas atenção: o lote está VENCIDO.', 'warning')
            elif status == 1:
                flash(f'"{nome}" adicionado ao estoque. Lote próximo ao vencimento.', 'warning')
            else:
                flash(f'"{nome}" validado e adicionado ao estoque com sucesso!', 'success')
        except Exception:
            db.session.rollback()
            flash('Erro ao registrar o medicamento. Tente novamente.', 'danger')

        return redirect(url_for('donation.triagem'))

    recentes = (
        Medicamento.query
        .order_by(Medicamento.id.desc())
        .limit(20)
        .all()
    )
    return render_template(
        'doacoes_triagem.html',
        recentes=recentes,
        tarjas=TARJAS_VALIDAS,
    )


# ── Excluir doação (somente Admin) ────────────────────────────────────────────

@donation_bp.route('/doacoes/<int:doacao_id>/excluir', methods=['POST'])
@login_required
@admin_required
def excluir_doacao(doacao_id):
    doacao = db.session.get(Doacao, doacao_id)
    if not doacao:
        flash('Doação não encontrada.', 'danger')
        return redirect(url_for('donation.nova_doacao'))
    try:
        detalhe = f'Doação #{doacao_id} ({doacao.quantidade} un. de "{doacao.medicamento.nome}") excluída por {current_user.nome}'
        db.session.delete(doacao)
        db.session.commit()
        registrar_log('Doação Excluída', detalhe)
        flash('Registro de doação excluído com sucesso.', 'success')
    except Exception:
        db.session.rollback()
        flash('Erro ao excluir doação. Tente novamente.', 'danger')
    return redirect(url_for('donation.nova_doacao'))


# ── Movimentações Consolidadas ────────────────────────────────────────────────

@donation_bp.route('/movimentacoes')
@login_required
def movimentacoes():
    saidas = Doacao.query.order_by(Doacao.data_doacao.desc()).limit(100).all()
    entradas = Medicamento.query.order_by(Medicamento.id.desc()).limit(50).all()
    total_saidas = sum(d.quantidade for d in saidas)
    total_entradas = sum(m.quantidade for m in entradas)
    return render_template(
        'movimentacoes.html',
        saidas=saidas,
        entradas=entradas,
        total_saidas=total_saidas,
        total_entradas=total_entradas,
    )
