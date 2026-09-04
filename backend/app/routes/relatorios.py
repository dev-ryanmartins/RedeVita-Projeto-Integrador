import csv
import io
from flask import Blueprint, render_template, Response, redirect, url_for
from flask_login import login_required
from sqlalchemy import func
from app.core.decorators import equipe_clinica_required, admin_required
from app.models.medicamento import Medicamento
from app.models.medico import Medico
from app.models.farmacia import Farmacia
from app.models.doacao import Doacao
from app.models.paciente import Paciente
from app.utils.log_helper import registrar_log
from app.database import db
from datetime import date

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.lib.enums import TA_CENTER, TA_LEFT

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# Cores corporativas RedeVita
COR_PRIMARIA = '#0ea5e9'  # Azul principal
COR_SECUNDARIA = '#3b82f6'  # Azul secundário
COR_TEXTO = '#1e293b'  # Cinza escuro para texto
COR_FUNDO = '#f8fafc'  # Cinza claro para fundo

relatorios_bp = Blueprint("relatorios", __name__)


def _criar_cabecalho_profissional(elementos, titulo):
    """Cria cabeçalho profissional para PDFs"""
    styles = getSampleStyleSheet()
    
    titulo_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor(COR_TEXTO),
        spaceAfter=6,
        spaceBefore=6,
        fontName='Helvetica-Bold',
        alignment=TA_LEFT
    )
    
    subtitulo_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#64748b'),
        spaceAfter=12,
        fontName='Helvetica',
        alignment=TA_LEFT
    )
    
    elementos.append(Spacer(1, 0.3*cm))
    elementos.append(Paragraph(titulo, titulo_style))
    elementos.append(Paragraph(f"Emitido em: {date.today().strftime('%d/%m/%Y')}", subtitulo_style))
    
    # Linha de separação
    linha = Table([['']], colWidths=[18*cm])
    linha.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 2, colors.HexColor(COR_PRIMARIA)),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#e2e8f0')),
    ]))
    elementos.append(linha)
    elementos.append(Spacer(1, 0.5*cm))


def _criar_rodape_profissional(elementos):
    """Cria rodapé profissional para PDFs"""
    styles = getSampleStyleSheet()
    
    rodape_style = ParagraphStyle(
        'CustomFooter',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#94a3b8'),
        spaceBefore=12,
        fontName='Helvetica',
        alignment=TA_CENTER
    )
    elementos.append(Spacer(1, 1*cm))
    elementos.append(Paragraph(
        "RedeVita - Sistema de Gestão de Medicamentos | Relatório Oficial",
        rodape_style
    ))


def _aplicar_estilo_tabela_profissional(table):
    """Aplica estilo profissional às tabelas"""
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(COR_PRIMARIA)),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 11),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("TOPPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTSIZE", (0, 1), (-1, -1), 9),
            ]
        )
    )
    return table


@relatorios_bp.route("/relatorios")
@login_required
@admin_required
def relatorios():
    try:
        hoje = date.today()
    except Exception:
        hoje = None

    try:
        proximos_vencimento = (
            Medicamento.query.filter(Medicamento.status_semaforo == 1)
            .order_by(Medicamento.data_validade)
            .all()
        )
    except Exception:
        proximos_vencimento = []
    
    try:
        vencidos = (
            Medicamento.query.filter(Medicamento.status_semaforo == 2)
            .order_by(Medicamento.data_validade)
            .all()
        )
    except Exception:
        vencidos = []

    try:
        total_medicos = Medico.query.count()
    except Exception:
        total_medicos = 0
    
    try:
        total_farmacias = Farmacia.query.count()
    except Exception:
        total_farmacias = 0
    
    try:
        total_medicamentos = Medicamento.query.count()
    except Exception:
        total_medicamentos = 0
    
    try:
        total_doacoes = Doacao.query.count()
    except Exception:
        total_doacoes = 0
    
    try:
        total_pacientes = Paciente.query.count()
    except Exception:
        total_pacientes = 0

    try:
        tarja_stats = (
            db.session.query(
                Medicamento.tarja,
                func.count(Medicamento.id),
                func.sum(Medicamento.quantidade),
            )
            .group_by(Medicamento.tarja)
            .all()
        )
    except Exception:
        tarja_stats = []

    return render_template(
        "relatorios.html",
        proximos_vencimento=proximos_vencimento,
        vencidos=vencidos,
        total_medicos=total_medicos,
        total_farmacias=total_farmacias,
        total_medicamentos=total_medicamentos,
        total_doacoes=total_doacoes,
        total_pacientes=total_pacientes,
        tarja_stats=tarja_stats,
        hoje=hoje,
    )


def _make_csv_response(filename: str, headers: list, rows: list) -> Response:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    output.seek(0)
    bom = "\ufeff"
    return Response(
        bom + output.getvalue(),
        mimetype="text/csv; charset=utf-8-sig",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@relatorios_bp.route("/relatorios/exportar/medicos")
@login_required
@equipe_clinica_required
def exportar_medicos():
    medicos = Medico.query.order_by(Medico.nome).all()
    registrar_log("Exportação CSV", "Exportou lista de médicos")
    rows = [
        [
            m.id,
            m.nome,
            m.crm,
            m.especialidade,
            m.contato or "",
            m.created_at.strftime("%d/%m/%Y") if m.created_at else "",
        ]
        for m in medicos
    ]
    return _make_csv_response(
        f"medicos_{date.today()}.csv",
        ["ID", "Nome", "CRM", "Especialidade", "Contato", "Cadastrado em"],
        rows,
    )


@relatorios_bp.route("/relatorios/exportar/farmacias")
@login_required
@equipe_clinica_required
def exportar_farmacias():
    farmacias = Farmacia.query.order_by(Farmacia.nome_fantasia).all()
    registrar_log("Exportação CSV", "Exportou lista de farmácias")
    rows = [
        [
            f.id,
            f.nome_fantasia,
            f.razao_social or "",
            f.cnpj,
            f.responsavel,
            f.endereco,
            f.created_at.strftime("%d/%m/%Y") if f.created_at else "",
        ]
        for f in farmacias
    ]
    return _make_csv_response(
        f"farmacias_{date.today()}.csv",
        [
            "ID",
            "Nome Fantasia",
            "Razão Social",
            "CNPJ",
            "Responsável",
            "Endereço",
            "Cadastrado em",
        ],
        rows,
    )


@relatorios_bp.route("/relatorios/exportar/medicamentos")
@login_required
@equipe_clinica_required
def exportar_medicamentos():
    medicamentos = Medicamento.query.order_by(Medicamento.nome).all()
    registrar_log("Exportação CSV", "Exportou lista de medicamentos")
    status_map = {0: "Seguro", 1: "Próximo Vencimento", 2: "Vencido"}
    rows = [
        [
            m.id,
            m.nome,
            m.lote,
            m.data_validade.strftime("%d/%m/%Y"),
            m.quantidade,
            status_map.get(m.status_semaforo, ""),
        ]
        for m in medicamentos
    ]
    return _make_csv_response(
        f"medicamentos_{date.today()}.csv",
        ["ID", "Nome", "Lote", "Validade", "Quantidade", "Status"],
        rows,
    )


@relatorios_bp.route("/relatorios/exportar/pacientes")
@login_required
@equipe_clinica_required
def exportar_pacientes():
    pacientes = Paciente.query.order_by(Paciente.nome).all()
    registrar_log("Exportação CSV", "Exportou lista de pacientes")
    rows = [
        [
            p.id,
            p.nome,
            p.cpf,
            p.data_nascimento.strftime("%d/%m/%Y") if p.data_nascimento else "",
            p.endereco or "",
            p.created_at.strftime("%d/%m/%Y") if p.created_at else "",
        ]
        for p in pacientes
    ]
    return _make_csv_response(
        f"pacientes_{date.today()}.csv",
        ["ID", "Nome", "CPF", "Data de Nascimento", "Endereço", "Cadastrado em"],
        rows,
    )


@relatorios_bp.route("/relatorios/exportar/doacoes")
@login_required
@equipe_clinica_required
def exportar_doacoes():
    doacoes = Doacao.query.order_by(Doacao.data_doacao.desc()).all()
    registrar_log("Exportação CSV", "Exportou histórico de doações")
    rows = [
        [
            d.id,
            d.data_doacao.strftime("%d/%m/%Y %H:%M"),
            d.medicamento.nome if d.medicamento else "—",
            d.medicamento.lote if d.medicamento else "—",
            d.quantidade,
            d.usuario.nome if d.usuario else "—",
            d.usuario.cargo if d.usuario else "—",
        ]
        for d in doacoes
    ]
    return _make_csv_response(
        f"doacoes_{date.today()}.csv",
        ["ID", "Data/Hora", "Medicamento", "Lote", "Qtd", "Responsável", "Cargo"],
        rows,
    )


@relatorios_bp.route("/relatorios/exportar/medicamentos/pdf")
@login_required
@equipe_clinica_required
def exportar_medicamentos_pdf():
    if not REPORTLAB_AVAILABLE:
        return redirect(url_for("relatorios.relatorios"))

    medicamentos = Medicamento.query.order_by(Medicamento.nome).all()
    registrar_log("Exportação PDF", "Exportou lista de medicamentos em PDF")

    response = Response(content_type="application/pdf")
    response.headers["Content-Disposition"] = (
        f"attachment; filename=medicamentos_{date.today()}.pdf"
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, 
                           rightMargin=1.5*cm, leftMargin=1.5*cm,
                           topMargin=2*cm, bottomMargin=2*cm)
    elements = []

    _criar_cabecalho_profissional(elementos, "Relatório de Medicamentos")

    data = [["Nome", "Lote", "Validade", "Qtd", "Status"]]
    status_map = {0: "Seguro", 1: "Próximo Vencimento", 2: "Vencido"}

    for m in medicamentos:
        data.append(
            [
                m.nome,
                m.lote,
                m.data_validade.strftime("%d/%m/%Y"),
                str(m.quantidade),
                status_map.get(m.status_semaforo, ""),
            ]
        )

    table = Table(
        data, colWidths=[2.5 * inch, 1 * inch, 1 * inch, 0.5 * inch, 1.2 * inch]
    )
    table = _aplicar_estilo_tabela_profissional(table)
    elements.append(table)
    
    _criar_rodape_profissional(elementos)
    doc.build(elements)

    pdf = buffer.getvalue()
    buffer.close()
    response.data = pdf

    return response


@relatorios_bp.route("/relatorios/exportar/medicos/pdf")
@login_required
@equipe_clinica_required
def exportar_medicos_pdf():
    if not REPORTLAB_AVAILABLE:
        return redirect(url_for("relatorios.relatorios"))

    medicos = Medico.query.order_by(Medico.nome).all()
    registrar_log("Exportação PDF", "Exportou lista de médicos em PDF")

    response = Response(content_type="application/pdf")
    response.headers["Content-Disposition"] = (
        f"attachment; filename=medicos_{date.today()}.pdf"
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                           rightMargin=1.5*cm, leftMargin=1.5*cm,
                           topMargin=2*cm, bottomMargin=2*cm)
    elements = []

    _criar_cabecalho_profissional(elementos, "Relatório de Médicos")

    data = [["Nome", "CRM", "Especialidade", "Contato", "Cadastrado em"]]

    for m in medicos:
        data.append(
            [
                m.nome,
                m.crm,
                m.especialidade,
                m.contato or "",
                m.created_at.strftime("%d/%m/%Y") if m.created_at else "",
            ]
        )

    table = Table(
        data, colWidths=[2 * inch, 1 * inch, 1.5 * inch, 1.5 * inch, 1 * inch]
    )
    table = _aplicar_estilo_tabela_profissional(table)
    elements.append(table)
    
    _criar_rodape_profissional(elementos)
    doc.build(elements)

    pdf = buffer.getvalue()
    buffer.close()
    response.data = pdf

    return response


@relatorios_bp.route("/relatorios/exportar/farmacias/pdf")
@login_required
@equipe_clinica_required
def exportar_farmacias_pdf():
    if not REPORTLAB_AVAILABLE:
        return redirect(url_for("relatorios.relatorios"))

    farmacias = Farmacia.query.order_by(Farmacia.nome_fantasia).all()
    registrar_log("Exportação PDF", "Exportou lista de farmácias em PDF")

    response = Response(content_type="application/pdf")
    response.headers["Content-Disposition"] = (
        f"attachment; filename=farmacias_{date.today()}.pdf"
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                           rightMargin=1.5*cm, leftMargin=1.5*cm,
                           topMargin=2*cm, bottomMargin=2*cm)
    elements = []

    _criar_cabecalho_profissional(elementos, "Relatório de Farmácias")

    data = [["Nome Fantasia", "Razão Social", "CNPJ", "Responsável", "Endereço", "Cadastrado em"]]

    for f in farmacias:
        data.append(
            [
                f.nome_fantasia,
                f.razao_social or "",
                f.cnpj,
                f.responsavel,
                f.endereco,
                f.created_at.strftime("%d/%m/%Y") if f.created_at else "",
            ]
        )

    table = Table(
        data, colWidths=[1.5 * inch, 1.5 * inch, 1 * inch, 1 * inch, 1.5 * inch, 1 * inch]
    )
    table = _aplicar_estilo_tabela_profissional(table)
    elements.append(table)
    
    _criar_rodape_profissional(elementos)
    doc.build(elements)

    pdf = buffer.getvalue()
    buffer.close()
    response.data = pdf

    return response


@relatorios_bp.route("/relatorios/exportar/pacientes/pdf")
@login_required
@equipe_clinica_required
def exportar_pacientes_pdf():
    if not REPORTLAB_AVAILABLE:
        return redirect(url_for("relatorios.relatorios"))

    pacientes = Paciente.query.order_by(Paciente.nome).all()
    registrar_log("Exportação PDF", "Exportou lista de pacientes em PDF")

    response = Response(content_type="application/pdf")
    response.headers["Content-Disposition"] = (
        f"attachment; filename=pacientes_{date.today()}.pdf"
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                           rightMargin=1.5*cm, leftMargin=1.5*cm,
                           topMargin=2*cm, bottomMargin=2*cm)
    elements = []

    _criar_cabecalho_profissional(elementos, "Relatório de Pacientes")

    data = [["Nome", "CPF", "Data de Nascimento", "Endereço", "Cadastrado em"]]

    for p in pacientes:
        data.append(
            [
                p.nome,
                p.cpf,
                p.data_nascimento.strftime("%d/%m/%Y") if p.data_nascimento else "",
                p.endereco or "",
                p.created_at.strftime("%d/%m/%Y") if p.created_at else "",
            ]
        )

    table = Table(
        data, colWidths=[2 * inch, 1 * inch, 1 * inch, 1.5 * inch, 1 * inch]
    )
    table = _aplicar_estilo_tabela_profissional(table)
    elements.append(table)
    
    _criar_rodape_profissional(elementos)
    doc.build(elements)

    pdf = buffer.getvalue()
    buffer.close()
    response.data = pdf

    return response


@relatorios_bp.route("/relatorios/exportar/doacoes/pdf")
@login_required
@equipe_clinica_required
def exportar_doacoes_pdf():
    if not REPORTLAB_AVAILABLE:
        return redirect(url_for("relatorios.relatorios"))

    doacoes = Doacao.query.order_by(Doacao.data_doacao.desc()).all()
    registrar_log("Exportação PDF", "Exportou histórico de doações em PDF")

    response = Response(content_type="application/pdf")
    response.headers["Content-Disposition"] = (
        f"attachment; filename=doacoes_{date.today()}.pdf"
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()
    title = Paragraph("Relatório de Doações", styles["Heading1"])
    elements.append(title)

    data = [["Data/Hora", "Medicamento", "Lote", "Qtd", "Responsável", "Cargo"]]

    for d in doacoes:
        data.append(
            [
                d.data_doacao.strftime("%d/%m/%Y %H:%M"),
                d.medicamento.nome if d.medicamento else "—",
                d.medicamento.lote if d.medicamento else "—",
                str(d.quantidade),
                d.usuario.nome if d.usuario else "—",
                d.usuario.cargo if d.usuario else "—",
            ]
        )

    table = Table(
        data, colWidths=[1.2 * inch, 1.5 * inch, 0.8 * inch, 0.5 * inch, 1.2 * inch, 1 * inch]
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 12),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )

    elements.append(table)
    doc.build(elements)

    pdf = buffer.getvalue()
    buffer.close()
    response.data = pdf

    return response


@relatorios_bp.route("/relatorios/exportar/sumario/pdf")
@login_required
@admin_required
def exportar_sumario_pdf():
    """
    Exporta um sumário executivo em PDF com as principais métricas do sistema.
    """
    if not REPORTLAB_AVAILABLE:
        return redirect(url_for("relatorios.relatorios"))

    try:
        hoje = date.today()
    except Exception:
        hoje = None

    try:
        total_medicamentos = Medicamento.query.count()
    except Exception:
        total_medicamentos = 0
    
    try:
        vencidos = Medicamento.query.filter(Medicamento.status_semaforo == 2).count()
    except Exception:
        vencidos = 0
    
    try:
        proximos_vencimento = Medicamento.query.filter(Medicamento.status_semaforo == 1).count()
    except Exception:
        proximos_vencimento = 0
    
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

    response = Response(content_type="application/pdf")
    response.headers["Content-Disposition"] = (
        f"attachment; filename=sumario_redevita_{date.today()}.pdf"
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                           rightMargin=1.5*cm, leftMargin=1.5*cm,
                           topMargin=2*cm, bottomMargin=2*cm)
    elements = []

    _criar_cabecalho_profissional(elementos, "Sumário Executivo - RedeVita")

    # Resumo das métricas
    styles = getSampleStyleSheet()
    summary_style = ParagraphStyle(
        'Summary',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor(COR_TEXTO),
        spaceAfter=12,
        leading=16
    )

    summary_data = [
        ["Métrica", "Quantidade", "Status"],
        ["Total de Medicamentos", str(total_medicamentos), "—" if total_medicamentos > 0 else "Vazio"],
        ["Medicamentos Vencidos", str(vencidos), "Crítico" if vencidos > 0 else "OK"],
        ["Próximos do Vencimento", str(proximos_vencimento), "Atenção" if proximos_vencimento > 0 else "OK"],
        ["Total de Doações", str(total_doacoes), "—" if total_doacoes > 0 else "Vazio"],
        ["Médicos Cadastrados", str(total_medicos), "—" if total_medicos > 0 else "Vazio"],
        ["Farmácias Parceiras", str(total_farmacias), "—" if total_farmacias > 0 else "Vazio"],
        ["Pacientes Cadastrados", str(total_pacientes), "—" if total_pacientes > 0 else "Vazio"],
    ]

    summary_table = Table(summary_data, colWidths=[2.5 * inch, 1.5 * inch, 1.2 * inch])
    summary_table = _aplicar_estilo_tabela_profissional(summary_table)
    elements.append(summary_table)

    # Adicionar observações
    elements.append(Spacer(1, 0.5*cm))
    elements.append(Paragraph("Observações:", styles['Heading3']))
    
    observacoes = []
    if vencidos > 0:
        observacoes.append(f"• {vencidos} medicamento(s) vencido(s) encontrado(s). Ação recomendada: descarte imediato.")
    if proximos_vencimento > 0:
        observacoes.append(f"• {proximos_vencimento} medicamento(s) próximo(s) do vencimento. Monitorar estoque.")
    if total_medicamentos == 0:
        observacoes.append("• Nenhum medicamento cadastrado. Iniciar triagem de doações.")
    if total_doacoes == 0:
        observacoes.append("• Nenhuma doação registrada. Sistema pronto para receber doações.")
    
    if not observacoes:
        observacoes.append("• Sistema operando dentro dos parâmetros normais.")
    
    for obs in observacoes:
        elements.append(Paragraph(obs, summary_style))

    _criar_rodape_profissional(elements)
    doc.build(elements)

    pdf = buffer.getvalue()
    buffer.close()
    response.data = pdf

    registrar_log("Exportação PDF", "Exportou sumário executivo em PDF")
    return response

    pdf = buffer.getvalue()
    buffer.close()
    response.data = pdf

    return response
