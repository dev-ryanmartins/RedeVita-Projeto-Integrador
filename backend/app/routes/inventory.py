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
from app.core.decorators import admin_required, farmaceutico_required
from datetime import datetime, date

inventory_bp = Blueprint("inventory", __name__)

TARJAS_VALIDAS = ["Sem Tarja", "Tarja Amarela", "Tarja Vermelha", "Portaria 344"]
TIPOS_RECEITA = [
    "Receita Simples",
    "Receita de Controle Especial (Branca)",
    "Receita 'B' Especial (Azul)",
    "Receita 'A' (Amarela)",
]


# ── API: busca na tabela de referência ANVISA ────────────────────────────────


@lru_cache(maxsize=1024)
def _buscar_referencia_cacheada(query: str):
    """
    Função auxiliar cacheada para busca de medicamentos de referência.
    Cache de 1024 entradas para otimizar consultas de autocomplete.
    """
    resultados = (
        MedicamentoReferencia.query.filter(
            MedicamentoReferencia.nome_comercial.ilike(f"%{query}%")
        )
        .order_by(MedicamentoReferencia.nome_comercial)
        .limit(10)
        .all()
    )
    return [r.to_dict() for r in resultados]


@inventory_bp.route("/api/referencia/buscar")
@login_required
def buscar_referencia():
    q = request.args.get("q", "").strip()
    if len(q) < 2:
        return jsonify([])
    return jsonify(_buscar_referencia_cacheada(q))


# ── Dashboard ────────────────────────────────────────────────────────────────


@inventory_bp.route("/dashboard")
@login_required
def dashboard():
    try:
        medicamentos = Medicamento.query.all()
    except Exception:
        medicamentos = []

    try:
        total_itens = len(medicamentos) if medicamentos else 0
    except Exception:
        total_itens = 0

    try:
        total_estoque = sum(m.quantidade for m in medicamentos if m.quantidade) if medicamentos else 0
    except Exception:
        total_estoque = 0

    try:
        alertas = len([m for m in medicamentos if m.status_semaforo == 2]) if medicamentos else 0
    except Exception:
        alertas = 0

    try:
        sem_estoque = len([m for m in medicamentos if m.quantidade == 0]) if medicamentos else 0
    except Exception:
        sem_estoque = 0

    try:
        total_doacoes = Doacao.query.count()
    except Exception:
        total_doacoes = 0

    try:
        total_medicos = Medico.query.count()
    except Exception:
        total_medicos = 0

    try:
        total_farmacias = Farmacia.query.count()
    except Exception:
        total_farmacias = 0

    try:
        total_pacientes = Paciente.query.count()
    except Exception:
        total_pacientes = 0

    try:
        proximos_vencimento = (
            Medicamento.query.filter(Medicamento.status_semaforo == 1)
            .order_by(Medicamento.data_validade)
            .limit(5)
            .all()
        )
    except Exception:
        proximos_vencimento = []

    try:
        ultimos_medicamentos = (
            Medicamento.query.order_by(Medicamento.id.desc()).limit(5).all()
        )
    except Exception:
        ultimos_medicamentos = []

    try:
        ultimos_medicos = Medico.query.order_by(Medico.id.desc()).limit(3).all()
    except Exception:
        ultimos_medicos = []

    try:
        ultimas_farmacias = Farmacia.query.order_by(Farmacia.id.desc()).limit(3).all()
    except Exception:
        ultimas_farmacias = []

    try:
        now = date.today()
    except Exception:
        now = None

    # Dados agregados para os gráficos do dashboard. O cálculo permanece no
    # backend para que os gráficos reflitam o banco atual e funcionem sem API
    # adicional no carregamento inicial.
    meses_abreviados = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
                        "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    doacoes_mensais = [0] * 6
    meses_chave = []
    try:
        hoje = now or date.today()
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
    except Exception:
        meses_chave = []
        doacoes_mensais = [0] * 6

    if meses_chave:
        labels_doacoes = [meses_abreviados[mes - 1] for _, mes in meses_chave]
    else:
        labels_doacoes = meses_abreviados[:6]

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
        total=total_itens,
        estoque=total_estoque,
        alertas=alertas,
        total_doacoes=total_doacoes,
        total_medicos=total_medicos,
        total_farmacias=total_farmacias,
        total_pacientes=total_pacientes,
        medicamentos=ultimos_medicamentos,
        proximos_vencimento=proximos_vencimento,
        ultimos_medicos=ultimos_medicos,
        ultimas_farmacias=ultimas_farmacias,
        sem_estoque=sem_estoque,
        now=now,
        labels_doacoes=labels_doacoes,
        doacoes_mensais=doacoes_mensais,
        estoque_status=estoque_status,
        validade_status=validade_status,
    )


# ── Inventário ───────────────────────────────────────────────────────────────


@inventory_bp.route("/inventario")
@login_required
def listar_medicamentos():
    pagina = request.args.get("page", 1, type=int)
    por_pagina = 20
    medicamentos = Medicamento.query.order_by(Medicamento.id.desc()).paginate(
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


# ── Exportar CSV ─────────────────────────────────────────────────────────────


@inventory_bp.route("/inventario/exportar-csv")
@login_required
@farmaceutico_required
def exportar_csv():
    medicamentos = Medicamento.query.order_by(Medicamento.nome).all()
    status_map = {0: "Seguro", 1: "Atenção", 2: "Vencido"}

    output = io.StringIO()
    writer = csv.writer(output, delimiter=";", quoting=csv.QUOTE_ALL)
    writer.writerow(
        [
            "Nome",
            "Princípio Ativo",
            "Tarja",
            "Lote",
            "Validade",
            "Quantidade",
            "Status",
            "Uso Contínuo",
        ]
    )
    for med in medicamentos:
        writer.writerow(
            [
                med.nome,
                med.principio_ativo or "—",
                med.tarja,
                med.lote,
                med.data_validade.strftime("%d/%m/%Y"),
                med.quantidade,
                status_map.get(med.status_semaforo, "—"),
                "Sim" if med.uso_continuo else "Não",
            ]
        )

    registrar_log(
        "Exportação CSV", f"Estoque exportado ({len(medicamentos)} medicamentos)"
    )

    filename = f'estoque_redevita_{date.today().strftime("%Y%m%d")}.csv'
    return Response(
        "\ufeff" + output.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Novo Medicamento ─────────────────────────────────────────────────────────


@inventory_bp.route("/medicamento/novo", methods=["POST"])
@login_required
@farmaceutico_required
def novo_medicamento():
    dados = {
        "nome": request.form.get("nome", "").strip(),
        "lote": request.form.get("lote", "").strip(),
        "data_validade": request.form.get("data_validade", "").strip(),
        "quantidade": request.form.get("quantidade", "").strip(),
    }

    valido, erros = validar_entrada_medicamento(dados)
    if not valido:
        for erro in erros:
            flash(erro, "danger")
        return redirect(url_for("inventory.listar_medicamentos"))

    tarja = request.form.get("tarja", "Sem Tarja").strip()
    if tarja not in TARJAS_VALIDAS:
        tarja = "Sem Tarja"

    principio_ativo = request.form.get("principio_ativo", "").strip() or None
    uso_continuo = request.form.get("uso_continuo") == "1"
    request.form.get("registro_ms", "").strip() or None
    referencia_id = request.form.get("referencia_id", type=int) or None

    try:
        data_dt = datetime.strptime(dados["data_validade"], "%Y-%m-%d").date()
        status = calcular_status_semaforo(data_dt)
        novo_med = Medicamento(
            nome=dados["nome"],
            lote=dados["lote"],
            data_validade=data_dt,
            quantidade=int(dados["quantidade"]),
            status_semaforo=status,
            tarja=tarja,
            principio_ativo=principio_ativo,
            uso_continuo=uso_continuo,
            referencia_id=referencia_id,
        )
        
        # Validação Portaria 344
        is_valid, error_msg = novo_med.validar_portaria_344()
        if not is_valid:
            flash(f"Erro de validação ANVISA: {error_msg}", "danger")
            return redirect(url_for("inventory.listar_medicamentos"))
        
        db.session.add(novo_med)
        db.session.commit()

        acao = (
            "Portaria 344 - Cadastro" if tarja == "Portaria 344" else "Novo Medicamento"
        )
        registrar_log(
            acao,
            f'Medicamento "{dados["nome"]}" (Tarja: {tarja}, Lote: {dados["lote"]}) cadastrado',
        )
        flash("Medicamento cadastrado com sucesso!", "success")
    except Exception:
        db.session.rollback()
        flash("Erro ao cadastrar medicamento. Tente novamente.", "danger")

    return redirect(url_for("inventory.listar_medicamentos"))


# ── Editar Medicamento ────────────────────────────────────────────────────────


@inventory_bp.route("/medicamento/<int:med_id>/editar", methods=["POST"])
@login_required
@farmaceutico_required
def editar_medicamento(med_id):
    med = db.session.get(Medicamento, med_id)
    if not med:
        flash("Medicamento não encontrado.", "danger")
        return redirect(url_for("inventory.listar_medicamentos"))

    dados = {
        "nome": request.form.get("nome", "").strip(),
        "lote": request.form.get("lote", "").strip(),
        "data_validade": request.form.get("data_validade", "").strip(),
        "quantidade": request.form.get("quantidade", "").strip(),
    }

    valido, erros = validar_entrada_medicamento(dados)
    if not valido:
        for erro in erros:
            flash(erro, "danger")
        return redirect(url_for("inventory.listar_medicamentos"))

    tarja = request.form.get("tarja", med.tarja).strip()
    if tarja not in TARJAS_VALIDAS:
        tarja = med.tarja

    principio_ativo = request.form.get("principio_ativo", "").strip() or None
    uso_continuo = request.form.get("uso_continuo") == "1"

    try:
        data_dt = datetime.strptime(dados["data_validade"], "%Y-%m-%d").date()
        med.nome = dados["nome"]
        med.lote = dados["lote"]
        med.data_validade = data_dt
        med.quantidade = int(dados["quantidade"])
        med.status_semaforo = calcular_status_semaforo(data_dt)
        med.tarja = tarja
        med.principio_ativo = principio_ativo
        med.uso_continuo = uso_continuo

        is_valid, error_msg = med.validar_portaria_344()
        if not is_valid:
            flash(f"Erro de validação ANVISA: {error_msg}", "danger")
            return redirect(url_for("inventory.listar_medicamentos"))

        db.session.commit()

        acao = (
            "Portaria 344 - Edição"
            if tarja == "Portaria 344"
            else "Edição de Medicamento"
        )
        registrar_log(acao, f'Medicamento "{med.nome}" (Tarja: {tarja}) atualizado')
        flash("Medicamento atualizado com sucesso!", "success")
    except Exception:
        db.session.rollback()
        flash("Erro ao atualizar medicamento. Tente novamente.", "danger")

    return redirect(url_for("inventory.listar_medicamentos"))


# ── Baixar Estoque ────────────────────────────────────────────────────────────


@inventory_bp.route("/medicamento/<int:med_id>/baixar-estoque", methods=["POST"])
@login_required
@farmaceutico_required
def baixar_estoque(med_id):
    med = db.session.get(Medicamento, med_id)
    if not med:
        flash("Medicamento não encontrado.", "danger")
        return redirect(url_for("inventory.listar_medicamentos"))

    quantidade = request.form.get("quantidade", type=int) or 0
    motivo = request.form.get("motivo", "").strip()

    if quantidade <= 0:
        flash("Informe uma quantidade válida (mínimo 1).", "danger")
        return redirect(url_for("inventory.listar_medicamentos"))

    if quantidade > med.quantidade:
        flash(f"Estoque insuficiente. Disponível: {med.quantidade} un.", "danger")
        return redirect(url_for("inventory.listar_medicamentos"))

    # ── Bloqueio para medicamentos controlados (Portaria 344) ────────────────
    if med.controlado:
        crm_raw = request.form.get("crm_medico", "").strip()
        tipo_receita = request.form.get("tipo_receita", "").strip()
        num_receita = request.form.get("numero_receita", "").strip()

        crm_digits = re.sub(r"\D", "", crm_raw)
        if len(crm_digits) < 4:
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
        med.quantidade -= quantidade
        db.session.commit()

        detalhes = f'Baixa de {quantidade} un. de "{med.nome}" — Motivo: {motivo or "não informado"}'
        if med.controlado:
            detalhes += f" | CRM: {crm_raw} | Receita: {tipo_receita}" + (
                f" | Nº {num_receita}" if num_receita else ""
            )

        acao = "Portaria 344 - Movimentação" if med.controlado else "Baixa de Estoque"
        registrar_log(acao, detalhes)
        flash(
            f'Baixa de {quantidade} un. de "{med.nome}" registrada com sucesso.',
            "success",
        )
    except Exception:
        db.session.rollback()
        flash("Erro ao registrar a baixa. Tente novamente.", "danger")

    return redirect(url_for("inventory.listar_medicamentos"))


# ── Excluir Medicamento ───────────────────────────────────────────────────────


@inventory_bp.route("/medicamento/<int:med_id>/excluir", methods=["POST"])
@login_required
@admin_required
def excluir_medicamento(med_id):
    med = db.session.get(Medicamento, med_id)
    if not med:
        flash("Medicamento não encontrado.", "danger")
        return redirect(url_for("inventory.listar_medicamentos"))

    try:
        nome = med.nome
        tarja = med.tarja
        db.session.delete(med)
        db.session.commit()
        acao = (
            "Portaria 344 - Exclusão"
            if tarja == "Portaria 344"
            else "Exclusão de Medicamento"
        )
        registrar_log(
            acao, f'Medicamento "{nome}" (Tarja: {tarja}) removido do sistema'
        )
        flash(f'Medicamento "{nome}" removido com sucesso.', "success")
    except Exception:
        db.session.rollback()
        flash(
            "Erro ao remover medicamento. Verifique se há doações vinculadas.", "danger"
        )

    return redirect(url_for("inventory.listar_medicamentos"))


# ── Duplicar Medicamento ──────────────────────────────────────────────────────


@inventory_bp.route("/medicamento/<int:med_id>/duplicar", methods=["POST"])
@login_required
@farmaceutico_required
def duplicar_medicamento(med_id):
    orig = db.session.get(Medicamento, med_id)
    if not orig:
        flash("Medicamento não encontrado.", "danger")
        return redirect(url_for("inventory.listar_medicamentos"))
    try:
        copia = Medicamento(
            nome=orig.nome,
            lote=f"COPIA-{orig.lote}",
            data_validade=orig.data_validade,
            quantidade=0,
            status_semaforo=orig.status_semaforo,
            tarja=orig.tarja,
            principio_ativo=orig.principio_ativo,
            uso_continuo=orig.uso_continuo,
            referencia_id=orig.referencia_id,
        )
        db.session.add(copia)
        db.session.commit()
        registrar_log(
            "Medicamento Duplicado",
            f'"{orig.nome}" (Lote {orig.lote}) duplicado com lote COPIA-{orig.lote}',
        )
        flash(
            f'"{orig.nome}" duplicado com sucesso. Atualize o lote e a quantidade.',
            "success",
        )
    except Exception:
        db.session.rollback()
        flash("Erro ao duplicar medicamento. Tente novamente.", "danger")
    return redirect(url_for("inventory.listar_medicamentos"))
