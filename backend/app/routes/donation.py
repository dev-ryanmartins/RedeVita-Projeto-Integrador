from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.doacao import Doacao
from app.models.medicamento import Medicamento
from app.database import db
from app.utils.log_helper import registrar_log
from app.core.decorators import cargo_required, admin_required, operador_required, voluntario_required, equipe_clinica_required, audit_critical_action
from app.utils.email_service import email_service
from app.utils.sms_service import sms_service
from app.utils.medication_validation import (
    validate_batch_for_creation,
    calculate_semaforo_status,
    validate_batch_for_stock_reduction,
    TARJAS_VALIDAS,
)
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

donation_bp = Blueprint("donation", __name__)


@donation_bp.route("/doacoes", methods=["GET", "POST"])
@login_required
@operador_required
@audit_critical_action('REGISTRO_DOAÇÃO')
def nova_doacao():
    if request.method == "POST":
        medicamento_id = request.form.get("medicamento_id", type=int)
        quantidade_str = request.form.get("quantidade", "0")
        receita_medica = request.form.get("receita_medica", "").strip()
        aprovacao_farmaceutico = request.form.get("aprovacao_farmaceutico", "").strip()
        destinatario = request.form.get("destinatario", "").strip() or "Não informado"
        observacao = request.form.get("observacao", "").strip() or None

        # Require explicit medication ID - no creation by name/type
        if not medicamento_id:
            flash("ERRO BLOQUEANTE: Selecione um medicamento existente. Não é possível registrar saída sem identificação explícita do lote.", "danger")
            return redirect(url_for("donation.nova_doacao"))

        try:
            qtd = int(quantidade_str)
            if qtd <= 0:
                flash("A quantidade deve ser maior que zero.", "danger")
                return redirect(url_for("donation.nova_doacao"))
        except ValueError:
            flash("Quantidade inválida.", "danger")
            return redirect(url_for("donation.nova_doacao"))

        # Get medication by explicit ID - no search by name
        medicamento = Medicamento.query.get(medicamento_id)

        if not medicamento:
            flash("ERRO BLOQUEANTE: Medicamento não encontrado no estoque. O ID informado não corresponde a nenhum lote existente.", "danger")
            return redirect(url_for("donation.nova_doacao"))

        if not medicamento.ativo:
            flash("ERRO BLOQUEANTE: Este medicamento está inativo e não pode ser usado para saída.", "danger")
            return redirect(url_for("donation.nova_doacao"))

        # Check if controlled substance
        is_controlled = medicamento.controlado

        if is_controlled:
            if not receita_medica:
                flash("ERRO BLOQUEANTE: Para medicamentos controlados (Portaria 344), é obrigatório informar a receita médica válida.", "danger")
                return redirect(url_for("donation.nova_doacao"))
            
            if aprovacao_farmaceutico != 'aprovado':
                flash("ERRO BLOQUEANTE: Para medicamentos controlados (Portaria 344), é obrigatória a aprovação do farmacêutico responsável.", "danger")
                return redirect(url_for("donation.nova_doacao"))

        # Use centralized validation for stock reduction (includes expiration check)
        validacao_saida = validate_batch_for_stock_reduction(
            data_validade=medicamento.data_validade,
            quantidade_solicitada=qtd,
            quantidade_disponivel=medicamento.quantidade
        )

        if not validacao_saida.is_valid:
            flash(f"ERRO BLOQUEANTE: {validacao_saida.error_message}", "danger")
            return redirect(url_for("donation.nova_doacao"))

        if medicamento.controlado:
            flash("⚠️ ALERTA DE PORTARIA 344: Este medicamento é controlado pela ANVISA. A doação requer aprovação obrigatória do farmacêutico responsável.", "warning")

        medicamento.quantidade -= qtd

        try:
            registro = Doacao(
                usuario_id=current_user.id,
                medicamento_id=medicamento.id,
                quantidade=qtd,
            )
            db.session.add(registro)
            db.session.commit()
            detalhe = (
                f'{qtd} un. de "{medicamento.nome}" (Tipo: {medicamento.principio_ativo or medicamento.tarja}) '
                f"por {current_user.nome} [{current_user.cargo_exibicao}] → {destinatario}"
            )
            if receita_medica:
                detalhe += f" | Receita: {receita_medica}"
            if aprovacao_farmaceutico:
                detalhe += f" | Aprovação Farmacêutico: {aprovacao_farmaceutico}"
            if observacao:
                detalhe += f" | Obs: {observacao}"
            registrar_log("Doação Registrada", detalhe)

            if current_user.email:
                email_service.send_doacao_confirmation_async(
                    to_email=current_user.email,
                    nome_doador=current_user.nome,
                    medicamento=medicamento.nome,
                    quantidade=qtd,
                    lote=medicamento.lote,
                    data_validade=medicamento.data_validade.strftime('%d/%m/%Y') if medicamento.data_validade else 'N/A',
                    data_doacao=datetime.utcnow()
                )
            
            if hasattr(current_user, 'telefone') and current_user.telefone:
                sms_service.send_doacao_confirmation_async(
                    to_phone=current_user.telefone,
                    medicamento=medicamento.nome
                )
            
            flash("Doação registrada com sucesso!", "success")
        except Exception:
            db.session.rollback()
            flash("Erro ao registrar doação. Tente novamente.", "danger")

        return redirect(url_for("donation.nova_doacao"))

    try:
        medicamentos = Medicamento.query.filter(Medicamento.quantidade > 0).all()
    except Exception:
        medicamentos = []

    data_inicio = request.args.get("data_inicio", "").strip()
    data_fim = request.args.get("data_fim", "").strip()
    
    try:
        q = Doacao.query.order_by(Doacao.data_doacao.desc())
    except Exception:
        q = None
    if data_inicio:
        try:
            q = q.filter(
                Doacao.data_doacao >= datetime.strptime(data_inicio, "%Y-%m-%d")
            )
        except (ValueError, AttributeError):
            pass
    if data_fim:
        try:
            q = q.filter(
                Doacao.data_doacao
                <= datetime.strptime(data_fim + " 23:59:59", "%Y-%m-%d %H:%M:%S")
            )
        except (ValueError, AttributeError):
            pass
    
    try:
        doacoes = q.all() if q else []
    except Exception:
        doacoes = []

    return render_template(
        "doacoes.html",
        medicamentos=medicamentos,
        doacoes=doacoes,
        data_inicio=data_inicio,
        data_fim=data_fim,
    )


@donation_bp.route("/doacoes/triagem", methods=["GET", "POST"])
@login_required
@operador_required
@audit_critical_action('TRIAGEM_DOAÇÃO')
def triagem():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        lote = request.form.get("lote", "").strip()
        data_validade_str = request.form.get("data_validade", "").strip()
        quantidade_str = request.form.get("quantidade", "0").strip()
        tarja = request.form.get("tarja", "Sem Tarja").strip()
        principio_ativo = request.form.get("principio_ativo", "").strip() or None
        doador = request.form.get("doador", "").strip() or "Não informado"
        observacoes = request.form.get("observacoes", "").strip() or None

        # Parse date
        try:
            data_validade = datetime.strptime(data_validade_str, "%Y-%m-%d").date()
        except ValueError:
            flash("Data de validade inválida. Use formato AAAA-MM-DD.", "danger")
            return redirect(url_for("donation.triagem"))

        # Parse quantity
        try:
            quantidade = int(quantidade_str)
        except ValueError:
            flash("Quantidade inválida. Informe um número inteiro positivo.", "danger")
            return redirect(url_for("donation.triagem"))

        # Centralized domain validation - rejects expired batches and unknown tarja
        validacao = validate_batch_for_creation(
            nome=nome,
            lote=lote,
            data_validade=data_validade,
            quantidade=quantidade,
            tarja=tarja
        )
        
        if not validacao.is_valid:
            flash(validacao.error_message, "danger")
            return redirect(url_for("donation.triagem"))

        # Display warnings if any
        for warning in validacao.warnings:
            flash(warning, "warning")

        try:
            status_semaforo = calculate_semaforo_status(data_validade)
            
            med = Medicamento(
                nome=nome,
                lote=lote,
                data_validade=data_validade,
                quantidade=quantidade,
                status_semaforo=status_semaforo,
                tarja=tarja,
                principio_ativo=principio_ativo,
            )

            is_valid, error_msg = med.validar_portaria_344()
            if not is_valid:
                flash(f"Erro de validação ANVISA: {error_msg}", "danger")
                return redirect(url_for("donation.triagem"))
            
            if tarja == "Portaria 344":
                flash("ERRO BLOQUEANTE: Substâncias controladas pela Portaria 344 não podem ser cadastradas automaticamente. Requer validação manual do farmacêutico responsável.", "danger")
                return redirect(url_for("donation.triagem"))
            
            principio_lower = (principio_ativo or "").lower()
            controlled_keywords = ['antibiotico', 'antidepressivo', 'anfetamina', 'opiaceo', 'benzodiazepin', 'controlado', 'psicotropico']
            if any(keyword in principio_lower for keyword in controlled_keywords):
                flash("ERRO BLOQUEANTE: Substâncias controladas detectadas pelo princípio ativo. Requer validação manual do farmacêutico responsável.", "danger")
                return redirect(url_for("donation.triagem"))
            
            db.session.add(med)
            db.session.commit()
            registrar_log(
                "Triagem — Entrada de Medicamento",
                f'"{nome}" (Lote {lote}, {quantidade} un.) recebido de "{doador}" e adicionado ao estoque'
                + (f" | Obs: {observacoes}" if observacoes else ""),
            )

            if doador and doador != "Não informado":
                logger.info(f"Notificação de triagem aprovada para doador: {doador} - Medicamento: {nome}")
            
            if status_semaforo == 1:
                flash(
                    f'"{nome}" adicionado ao estoque. Lote próximo ao vencimento.',
                    "warning",
                )
            else:
                flash(
                    f'"{nome}" validado e adicionado ao estoque com sucesso!', "success"
                )
        except Exception:
            db.session.rollback()
            flash("Erro ao registrar o medicamento. Tente novamente.", "danger")

        return redirect(url_for("donation.triagem"))

    recentes = Medicamento.query.order_by(Medicamento.id.desc()).limit(20).all()
    return render_template(
        "doacoes_triagem.html",
        recentes=recentes,
        tarjas=TARJAS_VALIDAS,
    )


@donation_bp.route("/doacoes/<int:doacao_id>/excluir", methods=["POST"])
@login_required
@admin_required
def excluir_doacao(doacao_id):
    doacao = db.session.get(Doacao, doacao_id)
    if not doacao:
        flash("Doação não encontrada.", "danger")
        return redirect(url_for("donation.nova_doacao"))
    try:
        detalhe = f'Doação #{doacao_id} ({doacao.quantidade} un. de "{doacao.medicamento.nome}") excluída por {current_user.nome}'
        db.session.delete(doacao)
        db.session.commit()
        registrar_log("Doação Excluída", detalhe)
        flash("Registro de doação excluído com sucesso.", "success")
    except Exception:
        db.session.rollback()
        flash("Erro ao excluir doação. Tente novamente.", "danger")
    return redirect(url_for("donation.nova_doacao"))


@donation_bp.route("/movimentacoes")
@login_required
@equipe_clinica_required
def movimentacoes():
    saidas = Doacao.query.order_by(Doacao.data_doacao.desc()).limit(100).all()
    entradas = Medicamento.query.order_by(Medicamento.id.desc()).limit(50).all()
    total_saidas = sum(d.quantidade for d in saidas)
    total_entradas = sum(m.quantidade for m in entradas)
    return render_template(
        "movimentacoes.html",
        saidas=saidas,
        entradas=entradas,
        total_saidas=total_saidas,
        total_entradas=total_entradas,
    )
