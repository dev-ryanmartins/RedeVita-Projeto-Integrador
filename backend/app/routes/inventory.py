import io
import re
import csv
from functools import lru_cache
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    Response,
    jsonify,
)
from flask_login import login_required
from app.models.medicamento import Medicamento
from app.models.medicamento_referencia import MedicamentoReferencia
from app.models.doacao import Doacao
from app.models.medico import Medico
from app.models.farmacia import Farmacia
from app.models.paciente import Paciente
from app.database import db
from app.utils.semaforo import calcular_status_semaforo
from app.schemas.med_schema import validar_entrada_medicamento
from app.utils.log_helper import registrar_log
from app.utils.semaforo import calcular_status_semaforo
from app.utils.anvisa_api import consultar_regularidade_medicamento
from app.utils.tarja_mapper import mapear_tarja_por_principio_ativo
from app.core.decorators import admin_required, farmaceutico_required, voluntario_required, equipe_clinica_required, audit_critical_action
from datetime import datetime, date

inventory_bp = Blueprint("inventory", __name__)

TARJAS_VALIDAS = ["Sem Tarja", "Tarja Amarela", "Tarja Vermelha", "Portaria 344"]
TIPOS_RECEITA = [
    "Receita Simples",
    "Receita de Controle Especial (Branca)",
    "Receita 'B' Especial (Azul)",
    "Receita 'A' (Amarela)",
]


@lru_cache(maxsize=1024)
def buscar_medicamentos_referencia(nome_busca: str):
    resultados = (
        MedicamentoReferencia.query.filter(
            MedicamentoReferencia.nome_comercial.ilike(f"%{nome_busca}%")
        )
        .order_by(MedicamentoReferencia.nome_comercial)
        .limit(10)
        .all()
    )
    return [r.to_dict() for r in resultados]


@inventory_bp.route("/api/referencia/buscar")
@login_required
@equipe_clinica_required
def api_buscar_referencia():
    termo = request.args.get("q", "").strip()
    if len(termo) < 2:
        return jsonify([])
    return jsonify(buscar_medicamentos_referencia(termo))


@inventory_bp.route("/dashboard")
@login_required
@voluntario_required
def dashboard():
    # Filtra apenas medicamentos ativos
    medicamentos = Medicamento.query.filter_by(ativo=True).all()
    hoje = date.today()

    total_medicamentos = len(medicamentos)
    total_estoque = sum(m.quantidade for m in medicamentos if m.quantidade)
    alertas_vencimento = len([m for m in medicamentos if m.status_semaforo == 2])
    sem_estoque = len([m for m in medicamentos if m.quantidade == 0])

    total_doacoes = Doacao.query.count()
    total_medicos = Medico.query.count()
    total_farmacias = Farmacia.query.count()
    total_pacientes = Paciente.query.count()

    proximos_vencimento = (
        Medicamento.query.filter_by(ativo=True).filter(Medicamento.status_semaforo == 1)
        .order_by(Medicamento.data_validade)
        .limit(5)
        .all()
    )
    ultimos_medicamentos = (
        Medicamento.query.filter_by(ativo=True).order_by(Medicamento.id.desc()).limit(5).all()
    )
    ultimos_medicos = Medico.query.order_by(Medico.id.desc()).limit(3).all()
    ultimas_farmacias = Farmacia.query.order_by(Farmacia.id.desc()).limit(3).all()

    meses_abreviados = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
                        "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    doacoes_mensais = [0] * 6
    meses_chave = []

    for deslocamento in range(5, -1, -1):
        numero_mes = hoje.month - deslocamento
        ano = hoje.year + (numero_mes - 1) // 12
        mes = (numero_mes - 1) % 12 + 1
        meses_chave.append((ano, mes))

    indice_mes = {chave: indice for indice, chave in enumerate(meses_chave)}
    for doacao in Doacao.query.all():
        data_doacao = doacao.data_doacao
        if not data_doacao:
            continue
        data_evento = data_doacao.date() if hasattr(data_doacao, "date") else data_doacao
        indice = indice_mes.get((data_evento.year, data_evento.month))
        if indice is not None:
            doacoes_mensais[indice] += 1

    labels_doacoes = [meses_abreviados[mes - 1] for _, mes in meses_chave]

    estoque_status = {"Seguro": 0, "Atenção": 0, "Vencido": 0, "Sem estoque": 0}
    validade_status = {"Vencidos": 0, "Próximo Vencimento": 0, "Seguros": 0}

    for medicamento in medicamentos:
        if not medicamento.quantidade:
            estoque_status["Sem estoque"] += 1
        elif medicamento.status_semaforo == 2:
            estoque_status["Vencido"] += 1
            validade_status["Vencidos"] += 1
        elif medicamento.status_semaforo == 1:
            estoque_status["Atenção"] += 1
            validade_status["Próximo Vencimento"] += 1
        else:
            estoque_status["Seguro"] += 1
            validade_status["Seguros"] += 1

    return render_template(
        "dashboard.html",
        total=total_medicamentos,
        estoque=total_estoque,
        alertas=alertas_vencimento,
        total_doacoes=total_doacoes,
        total_medicos=total_medicos,
        total_farmacias=total_farmacias,
        total_pacientes=total_pacientes,
        medicamentos=ultimos_medicamentos,
        proximos_vencimento=proximos_vencimento,
        ultimos_medicos=ultimos_medicos,
        ultimas_farmacias=ultimas_farmacias,
        sem_estoque=sem_estoque,
        now=hoje,
        labels_doacoes=labels_doacoes,
        doacoes_mensais=doacoes_mensais,
        estoque_status=estoque_status,
        validade_status=validade_status,
    )


@inventory_bp.route("/inventario")
@login_required
@equipe_clinica_required
def listar_medicamentos():
    """Lista todos os medicamentos com paginação"""
    pagina = request.args.get("page", 1, type=int)
    por_pagina = 20

    # Filtra apenas medicamentos ativos (não arquivados)
    medicamentos = Medicamento.query.filter_by(ativo=True).order_by(Medicamento.id.desc()).paginate(
        page=pagina, per_page=por_pagina, error_out=False
    )

    referencias = MedicamentoReferencia.query.order_by(
        MedicamentoReferencia.nome_comercial
    ).all() or []

    total_controlados = sum(1 for m in medicamentos.items if m.controlado) or 0
    total_continuo = sum(1 for m in medicamentos.items if m.uso_continuo) or 0

    return render_template(
        "inventario.html",
        medicamentos=medicamentos,
        referencias=referencias,
        total_controlados=total_controlados,
        total_continuo=total_continuo,
        tarjas=TARJAS_VALIDAS,
        tipos_receita=TIPOS_RECEITA,
    )


@inventory_bp.route("/inventario/exportar-csv")
@login_required
@farmaceutico_required
def exportar_csv():
    # Exporta apenas medicamentos ativos
    medicamentos = Medicamento.query.filter_by(ativo=True).order_by(Medicamento.nome).all()
    status_map = {0: "Seguro", 1: "Atenção", 2: "Vencido"}

    output = io.StringIO()
    writer = csv.writer(output, delimiter=";", quoting=csv.QUOTE_ALL)

    writer.writerow([
        "Nome",
        "Princípio Ativo",
        "Tarja",
        "Lote",
        "Validade",
        "Quantidade",
        "Status",
        "Uso Contínuo",
    ])

    for med in medicamentos:
        writer.writerow([
            med.nome,
            med.principio_ativo or "—",
            med.tarja,
            med.lote,
            med.data_validade.strftime("%d/%m/%Y"),
            med.quantidade,
            status_map.get(med.status_semaforo, "—"),
            "Sim" if med.uso_continuo else "Não",
        ])

    registrar_log(
        "Exportação CSV", f"Estoque exportado ({len(medicamentos)} medicamentos)"
    )

    filename = f'estoque_redevita_{date.today().strftime("%Y%m%d")}.csv'
    return Response(
        "\ufeff" + output.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@inventory_bp.route("/exportar-csv")
@login_required
@equipe_clinica_required
def exportar_csv_resumo():
    """Exportação CSV independente - Módulo Aditivo"""
    # Exporta apenas medicamentos ativos
    medicamentos = Medicamento.query.filter_by(ativo=True).order_by(Medicamento.nome).all()
    status_map = {0: "Seguro", 1: "Atenção", 2: "Vencido"}

    output = io.StringIO()
    writer = csv.writer(output, delimiter=";", quoting=csv.QUOTE_ALL)

    writer.writerow([
        "ID",
        "Nome",
        "Lote",
        "Validade",
        "Quantidade",
        "Status",
        "Tarja",
    ])

    for med in medicamentos:
        writer.writerow([
            med.id,
            med.nome,
            med.lote,
            med.data_validade.strftime("%d/%m/%Y"),
            med.quantidade,
            status_map.get(med.status_semaforo, "—"),
            med.tarja,
        ])

    registrar_log(
        "Exportação CSV Resumo", f"Resumo exportado ({len(medicamentos)} medicamentos)"
    )

    filename = f'resumo_estoque_{date.today().strftime("%Y%m%d")}.csv'
    return Response(
        "\ufeff" + output.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@inventory_bp.route("/medicamento/novo", methods=["POST"])
@login_required
@farmaceutico_required
@audit_critical_action('CADASTRO_MEDICAMENTO')
def novo_medicamento():
    """Cadastra um novo medicamento no estoque"""
    dados_formulario = {
        "nome": request.form.get("nome", "").strip(),
        "lote": request.form.get("lote", "").strip(),
        "data_validade": request.form.get("data_validade", "").strip(),
        "quantidade": request.form.get("quantidade", "").strip(),
    }

    valido, erros = validar_entrada_medicamento(dados_formulario)
    if not valido:
        for erro in erros:
            flash(erro, "danger")
        return redirect(url_for("inventory.listar_medicamentos"))

    tarja = request.form.get("tarja", "Sem Tarja").strip()
    principio_ativo = request.form.get("principio_ativo", "").strip() or None
    
    # Mapeamento automático de tarja por princípio ativo
    tarja_mapeada = mapear_tarja_por_principio_ativo(dados_formulario["nome"], principio_ativo)
    
    # Se o usuário selecionou "Sem Tarja" mas o mapeamento indica controle, forçar a tarja correta
    if tarja == "Sem Tarja" and tarja_mapeada != "Sem Tarja":
        tarja = tarja_mapeada
        flash(
            f'⚠️ Tarja ajustada automaticamente para "{tarja}" com base no princípio ativo/nome do medicamento conforme regulamentação ANVISA.',
            "warning"
        )
    elif tarja not in TARJAS_VALIDAS:
        tarja = tarja_mapeada
    else:
        # Se o usuário selecionou uma tarja específica, respeitar mas verificar consistência
        if tarja == "Sem Tarja" and tarja_mapeada != "Sem Tarja":
            flash(
                f'⚠️ Atenção: O medicamento "{dados_formulario["nome"]}" parece ser controlado ({tarja_mapeada}), mas foi classificado como "Sem Tarja". Verifique a classificação.',
                "warning"
            )

    uso_continuo = request.form.get("uso_continuo") == "1"
    referencia_id = request.form.get("referencia_id", type=int) or None
    registro_ms = request.form.get("registro_ms", "").strip() or None

    try:
        data_validade = datetime.strptime(dados_formulario["data_validade"], "%Y-%m-%d").date()
        status_semaforo = calcular_status_semaforo(data_validade)
        
        if status_semaforo == 2:
            flash("ERRO BLOQUEANTE: Não é possível cadastrar medicamentos vencidos (status Vermelho). Medicamento fora da validade regulatória.", "danger")
            return redirect(url_for("inventory.listar_medicamentos"))

        novo_medicamento = Medicamento(
            nome=dados_formulario["nome"],
            lote=dados_formulario["lote"],
            data_validade=data_validade,
            quantidade=int(dados_formulario["quantidade"]),
            status_semaforo=status_semaforo,
            tarja=tarja,
            principio_ativo=principio_ativo,
            uso_continuo=uso_continuo,
            referencia_id=referencia_id,
        )

        validacao_ok, mensagem_erro = novo_medicamento.validar_portaria_344()
        if not validacao_ok:
            flash(f"Erro de validação ANVISA: {mensagem_erro}", "danger")
            return redirect(url_for("inventory.listar_medicamentos"))
        
        if tarja == "Portaria 344":
            flash("ERRO BLOQUEANTE: Substâncias controladas pela Portaria 344 não podem ser cadastradas automaticamente. Requer validação manual do farmacêutico responsável.", "danger")
            return redirect(url_for("inventory.listar_medicamentos"))
        
        principio_lower = (principio_ativo or "").lower()
        controlled_keywords = ['antibiotico', 'antidepressivo', 'anfetamina', 'opiaceo', 'benzodiazepin', 'controlado', 'psicotropico']
        if any(keyword in principio_lower for keyword in controlled_keywords):
            flash("ERRO BLOQUEANTE: Substâncias controladas detectadas pelo princípio ativo. Requer validação manual do farmacêutico responsável.", "danger")
            return redirect(url_for("inventory.listar_medicamentos"))

        if registro_ms:
            resultado_anvisa = consultar_regularidade_medicamento(registro_ms)

            registrar_log(
                "Consulta ANVISA",
                f'Registro MS {registro_ms}: {resultado_anvisa["situacao"]} - {resultado_anvisa["detalhes"]}'
            )

            if resultado_anvisa["regular"] is False:
                flash(
                    f"⚠️ Alerta ANVISA: {resultado_anvisa['detalhes']}. Medicamento cadastrado com restrição sanitária.",
                    "warning"
                )
                novo_medicamento.observacoes = f"RESTRIÇÃO ANVISA: {resultado_anvisa['detalhes']}"
            elif resultado_anvisa["regular"] is None:
                flash(
                    f"ℹ️ Nota ANVISA: {resultado_anvisa['detalhes']}. Não foi possível verificar regularidade.",
                    "info"
                )

        db.session.add(novo_medicamento)
        db.session.commit()

        tipo_log = "Portaria 344 - Cadastro" if tarja == "Portaria 344" else "Novo Medicamento"
        registrar_log(
            tipo_log,
            f'Medicamento "{dados_formulario["nome"]}" (Tarja: {tarja}, Lote: {dados_formulario["lote"]}) cadastrado',
        )
        flash("Medicamento cadastrado com sucesso!", "success")
    except Exception:
        db.session.rollback()
        flash("Erro ao cadastrar medicamento. Tente novamente.", "danger")

    return redirect(url_for("inventory.listar_medicamentos"))


@inventory_bp.route("/medicamento/<int:med_id>/editar", methods=["POST"])
@login_required
@farmaceutico_required
@audit_critical_action('EDIÇÃO_MEDICAMENTO')
def editar_medicamento(med_id):
    medicamento = db.session.get(Medicamento, med_id)
    if not medicamento:
        flash("Medicamento não encontrado.", "danger")
        return redirect(url_for("inventory.listar_medicamentos"))

    dados_formulario = {
        "nome": request.form.get("nome", "").strip(),
        "lote": request.form.get("lote", "").strip(),
        "data_validade": request.form.get("data_validade", "").strip(),
        "quantidade": request.form.get("quantidade", "").strip(),
    }

    valido, erros = validar_entrada_medicamento(dados_formulario)
    if not valido:
        for erro in erros:
            flash(erro, "danger")
        return redirect(url_for("inventory.listar_medicamentos"))

    tarja = request.form.get("tarja", medicamento.tarja).strip()
    if tarja not in TARJAS_VALIDAS:
        tarja = medicamento.tarja

    principio_ativo = request.form.get("principio_ativo", "").strip() or None
    uso_continuo = request.form.get("uso_continuo") == "1"

    try:
        data_validade = datetime.strptime(dados_formulario["data_validade"], "%Y-%m-%d").date()

        medicamento.nome = dados_formulario["nome"]
        medicamento.lote = dados_formulario["lote"]
        medicamento.data_validade = data_validade
        medicamento.quantidade = int(dados_formulario["quantidade"])
        medicamento.status_semaforo = calcular_status_semaforo(data_validade)
        medicamento.tarja = tarja
        medicamento.principio_ativo = principio_ativo
        medicamento.uso_continuo = uso_continuo

        validacao_ok, mensagem_erro = medicamento.validar_portaria_344()
        if not validacao_ok:
            flash(f"Erro de validação ANVISA: {mensagem_erro}", "danger")
            return redirect(url_for("inventory.listar_medicamentos"))

        db.session.commit()

        tipo_log = "Portaria 344 - Edição" if tarja == "Portaria 344" else "Edição de Medicamento"
        registrar_log(tipo_log, f'Medicamento "{medicamento.nome}" (Tarja: {tarja}) atualizado')
        flash("Medicamento atualizado com sucesso!", "success")
    except Exception:
        db.session.rollback()
        flash("Erro ao atualizar medicamento. Tente novamente.", "danger")

    return redirect(url_for("inventory.listar_medicamentos"))


@inventory_bp.route("/medicamento/<int:med_id>/baixar-estoque", methods=["POST"])
@login_required
@farmaceutico_required
@audit_critical_action('BAIXA_ESTOQUE')
def baixar_estoque(med_id):
    medicamento = db.session.get(Medicamento, med_id)
    if not medicamento:
        flash("Medicamento não encontrado.", "danger")
        return redirect(url_for("inventory.listar_medicamentos"))

    quantidade_baixa = request.form.get("quantidade", type=int) or 0
    motivo_baixa = request.form.get("motivo", "").strip()

    if quantidade_baixa <= 0:
        flash("Informe uma quantidade válida (mínimo 1).", "danger")
        return redirect(url_for("inventory.listar_medicamentos"))

    if quantidade_baixa > medicamento.quantidade:
        flash(f"Estoque insuficiente. Disponível: {medicamento.quantidade} un.", "danger")
        return redirect(url_for("inventory.listar_medicamentos"))

    if medicamento.controlado:
        crm_medico = request.form.get("crm_medico", "").strip()
        tipo_receita = request.form.get("tipo_receita", "").strip()
        numero_receita = request.form.get("numero_receita", "").strip()

        crm_digitos = re.sub(r"\D", "", crm_medico)
        if len(crm_digitos) < 4:
            flash(
                "Medicamento Portaria 344: CRM do médico é obrigatório e deve ter ao menos 4 dígitos.",
                "danger",
            )
            return redirect(url_for("inventory.listar_medicamentos"))

        if not tipo_receita or tipo_receita not in TIPOS_RECEITA:
            flash(
                "Medicamento Portaria 344: Tipo de receita controlada é obrigatório.",
                "danger",
            )
            return redirect(url_for("inventory.listar_medicamentos"))

    try:
        medicamento.quantidade -= quantidade_baixa
        db.session.commit()

        detalhes_log = f'Baixa de {quantidade_baixa} un. de "{medicamento.nome}" — Motivo: {motivo_baixa or "não informado"}'
        if medicamento.controlado:
            detalhes_log += f" | CRM: {crm_medico} | Receita: {tipo_receita}"
            if numero_receita:
                detalhes_log += f" | Nº {numero_receita}"

        tipo_log = "Portaria 344 - Movimentação" if medicamento.controlado else "Baixa de Estoque"
        registrar_log(tipo_log, detalhes_log)
        flash(
            f'Baixa de {quantidade_baixa} un. de "{medicamento.nome}" registrada com sucesso.',
            "success",
        )
    except Exception:
        db.session.rollback()
        flash("Erro ao registrar a baixa. Tente novamente.", "danger")

    return redirect(url_for("inventory.listar_medicamentos"))


@inventory_bp.route("/medicamento/<int:med_id>/excluir", methods=["POST"])
@login_required
@admin_required
@audit_critical_action('EXCLUSÃO_MEDICAMENTO')
def excluir_medicamento(med_id):
    medicamento = db.session.get(Medicamento, med_id)
    if not medicamento:
        flash("Medicamento não encontrado.", "danger")
        return redirect(url_for("inventory.listar_medicamentos"))

    try:
        nome_medicamento = medicamento.nome
        tarja_medicamento = medicamento.tarja

        # Verificar se há doações vinculadas
        doacoes_vinculadas = Doacao.query.filter_by(medicamento_id=med_id).count()

        if doacoes_vinculadas > 0:
            # Soft delete: desativa o medicamento logicamente
            medicamento.ativo = False
            db.session.commit()

            tipo_log = "Portaria 344 - Arquivamento" if tarja_medicamento == "Portaria 344" else "Arquivamento de Medicamento"
            registrar_log(
                tipo_log, f'Medicamento "{nome_medicamento}" (Tarja: {tarja_medicamento}) arquivado - {doacoes_vinculadas} doação(ões) vinculada(s)'
            )
            flash(
                f'Medicamento "{nome_medicamento}" foi arquivado com sucesso. '
                f'Há {doacoes_vinculadas} doação(ões) vinculada(s) ao histórico deste medicamento, '
                f'portanto ele foi preservado para manter a integridade dos registros.',
                "warning"
            )
        else:
            # Hard delete: remove fisicamente se não houver doações
            db.session.delete(medicamento)
            db.session.commit()

            tipo_log = "Portaria 344 - Exclusão" if tarja_medicamento == "Portaria 344" else "Exclusão de Medicamento"
            registrar_log(
                tipo_log, f'Medicamento "{nome_medicamento}" (Tarja: {tarja_medicamento}) removido do sistema'
            )
            flash(f'Medicamento "{nome_medicamento}" removido com sucesso.', "success")

    except Exception as e:
        db.session.rollback()
        flash(
            f"Erro ao processar exclusão: {str(e)}",
            "danger"
        )

    return redirect(url_for("inventory.listar_medicamentos"))


@inventory_bp.route("/medicamento/<int:med_id>/duplicar", methods=["POST"])
@login_required
@farmaceutico_required
def duplicar_medicamento(med_id):
    medicamento_original = db.session.get(Medicamento, med_id)
    if not medicamento_original:
        flash("Medicamento não encontrado.", "danger")
        return redirect(url_for("inventory.listar_medicamentos"))

    try:
        copia_medicamento = Medicamento(
            nome=medicamento_original.nome,
            lote=f"COPIA-{medicamento_original.lote}",
            data_validade=medicamento_original.data_validade,
            quantidade=0,
            status_semaforo=medicamento_original.status_semaforo,
            tarja=medicamento_original.tarja,
            principio_ativo=medicamento_original.principio_ativo,
            uso_continuo=medicamento_original.uso_continuo,
            referencia_id=medicamento_original.referencia_id,
        )

        db.session.add(copia_medicamento)
        db.session.commit()

        registrar_log(
            "Medicamento Duplicado",
            f'"{medicamento_original.nome}" (Lote {medicamento_original.lote}) duplicado com lote COPIA-{medicamento_original.lote}',
        )
        flash(
            f'"{medicamento_original.nome}" duplicado com sucesso. Atualize o lote e a quantidade.',
            "success",
        )
    except Exception:
        db.session.rollback()
        flash("Erro ao duplicar medicamento. Tente novamente.", "danger")

    return redirect(url_for("inventory.listar_medicamentos"))
