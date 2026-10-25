from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.doacao import Doacao
from app.models.medicamento import Medicamento
from app.database import db
from app.utils.log_helper import registrar_log
from app.core.decorators import cargo_required, admin_required, operador_required, voluntario_required, equipe_clinica_required, audit_critical_action
from app.utils.email_service import email_service
from app.utils.sms_service import sms_service
from app.services.triagem_service import TriagemMedicamentoService, TriagemError
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
        medicamento_id = request.form.get("medicamento_id", "").strip()
        quantidade_str = request.form.get("quantidade", "0")
        receita_medica = request.form.get("receita_medica", "").strip()
        aprovacao_farmaceutico = request.form.get("aprovacao_farmaceutico", "").strip()
        destinatario = request.form.get("destinatario", "").strip() or "Não informado"
        observacao = request.form.get("observacao", "").strip() or None

        # Exigir ID explícito do medicamento
        if not medicamento_id:
            flash("Selecione um medicamento da lista.", "danger")
            return redirect(url_for("donation.nova_doacao"))

        try:
            medicamento_id_int = int(medicamento_id)
        except ValueError:
            flash("ID de medicamento inválido.", "danger")
            return redirect(url_for("donation.nova_doacao"))

        try:
            qtd = int(quantidade_str)
            if qtd <= 0:
                flash("A quantidade deve ser maior que zero.", "danger")
                return redirect(url_for("donation.nova_doacao"))
        except ValueError:
            flash("Quantidade inválida.", "danger")
            return redirect(url_for("donation.nova_doacao"))

        # Determinar se é controlado baseado no medicamento selecionado
        medicamento_temp = db.session.get(Medicamento, medicamento_id_int)
        is_controlled = medicamento_temp and medicamento_temp.controlado if medicamento_temp else False

        if is_controlled:
            if not receita_medica:
                flash("ERRO BLOQUEANTE: Para medicamentos controlados (Portaria 344), é obrigatório informar a receita médica válida.", "danger")
                return redirect(url_for("donation.nova_doacao"))
            
            if aprovacao_farmaceutico != 'aprovado':
                flash("ERRO BLOQUEANTE: Para medicamentos controlados (Portaria 344), é obrigatória a aprovação do farmacêutico responsável.", "danger")
                return redirect(url_for("donation.nova_doacao"))

        # Buscar medicamento por ID explícito - não usar busca por nome parcial
        medicamento = db.session.get(Medicamento, medicamento_id_int)

        if not medicamento:
            flash("Medicamento não encontrado. Selecione um medicamento válido.", "danger")
            return redirect(url_for("donation.nova_doacao"))

        # Validar elegibilidade e saldo
        if medicamento.status_semaforo == 2:
            flash("ERRO BLOQUEANTE: Não é possível doar medicamentos vencidos (status Vermelho). Medicamento fora da validade regulatória.", "danger")
            return redirect(url_for("donation.nova_doacao"))
        
        if medicamento.quantidade < qtd:
            flash(f"Quantidade insuficiente no estoque. Disponível: {medicamento.quantidade} un.", "danger")
            return redirect(url_for("donation.nova_doacao"))

        if medicamento.controlado:
            flash("⚠️ ALERTA DE PORTARIA 344: Este medicamento é controlado pela ANVISA. A doação requer aprovação obrigatória do farmacêutico responsável.", "warning")

        # Baixa de estoque dentro da transação
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
                f'{qtd} un. de "{medicamento.nome}" (Lote: {medicamento.lote}, Tipo: {medicamento.principio_ativo or "N/A"}) '
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
        # Paginação para listagem de medicamentos com estoque
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # Limitar per_page para máximo de 200
        per_page = min(per_page, 200)
        page = max(page, 1)
        
        paginated = Medicamento.query.filter(Medicamento.quantidade > 0).paginate(
            page=page, per_page=per_page, error_out=False
        )
        medicamentos = paginated.items
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
        # Paginação para listagem de doações
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # Limitar per_page para máximo de 200
        per_page = min(per_page, 200)
        page = max(page, 1)
        
        if q:
            paginated = q.paginate(page=page, per_page=per_page, error_out=False)
            doacoes = paginated.items
        else:
            doacoes = []
    except Exception:
        doacoes = []

    return render_template(
        "doacoes.html",
        medicamentos=medicamentos,
        doacoes=doacoes,
        data_inicio=data_inicio,
        data_fim=data_fim,
        medicamentos_page=page if 'medicamentos' in locals() else 1,
        medicamentos_per_page=per_page if 'medicamentos' in locals() else 50,
        doacoes_page=page if 'doacoes' in locals() else 1,
        doacoes_per_page=per_page if 'doacoes' in locals() else 50,
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

        try:
            # Usar serviço de triagem
            medicamento, aviso = TriagemMedicamentoService.processar_triagem(
                nome=nome,
                lote=lote,
                data_validade_str=data_validade_str,
                quantidade_str=quantidade_str,
                tarja=tarja,
                principio_ativo=principio_ativo,
                doador=doador,
                observacoes=observacoes
            )
            
            db.session.add(medicamento)
            db.session.commit()
            
            registrar_log(
                "Triagem — Entrada de Medicamento",
                f'"{nome}" (Lote {lote}, {quantidade_str} un.) recebido de "{doador}" e adicionado ao estoque'
                + (f" | Obs: {observacoes}" if observacoes else ""),
            )
            
            # Determinar tipo de flash baseado no aviso
            if "VENCIDO" in aviso:
                flash(f'⚠ {aviso}', "warning")
            elif "próximo ao vencimento" in aviso:
                flash(aviso, "warning")
            else:
                flash(aviso, "success")
                
        except TriagemError as e:
            flash(e.mensagem, "danger")
            return redirect(url_for("donation.triagem"))
        except Exception:
            db.session.rollback()
            flash("Erro ao registrar o medicamento. Tente novamente.", "danger")

        return redirect(url_for("donation.triagem"))

    recentes = Medicamento.query.order_by(Medicamento.id.desc()).limit(20).all()
    tarjas_validas = TriagemMedicamentoService.obter_tarjas_validas()
    return render_template(
        "doacoes_triagem.html",
        recentes=recentes,
        tarjas=tarjas_validas,
    )


@donation_bp.route("/doacoes/<int:doacao_id>/excluir", methods=["POST"])
@login_required
@admin_required
def excluir_doacao(doacao_id):
    doacao = db.session.get(Doacao, doacao_id)
    if not doacao:
        flash("Doação não encontrada.", "danger")
        return redirect(url_for("donation.nova_doacao"))
    
    # Não permitir exclusão física - usar compensação
    if doacao.cancelado:
        flash("Esta doação já foi cancelada.", "warning")
        return redirect(url_for("donation.nova_doacao"))
    
    # Verificar se já tem compensação vinculada
    if doacao.compensacao_id:
        flash("Esta doação já possui uma compensação vinculada.", "warning")
        return redirect(url_for("donation.nova_doacao"))
    
    try:
        # Marcar como cancelado
        doacao.cancelado = True
        doacao.cancelado_por_id = current_user.id
        doacao.cancelado_em = datetime.utcnow()
        doacao.justificativa_cancelamento = "Cancelado via interface de exclusão (append-only ledger)"
        
        # Restaura o estoque (compensação transacional)
        medicamento = doacao.medicamento
        medicamento.quantidade += doacao.quantidade
        
        db.session.commit()
        
        detalhe = f'Doação #{doacao_id} ({doacao.quantidade} un. de "{medicamento.nome}") cancelada por {current_user.nome} - Estoque restaurado'
        registrar_log("Doação Cancelada", detalhe)
        flash("Doação cancelada com sucesso. O histórico foi preservado e o estoque restaurado.", "success")
    except Exception:
        db.session.rollback()
        flash("Erro ao cancelar doação. Tente novamente.", "danger")
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
