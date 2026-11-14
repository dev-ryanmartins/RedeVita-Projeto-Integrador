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

    REPORTLAB_DISPONIVEL = True
except ImportError:
    REPORTLAB_DISPONIVEL = False

COR_AZUL = '#0ea5e9'
COR_TEXTO = '#1e293b'

relatorios_bp = Blueprint("relatorios", __name__)


def criar_cabecalho_pdf(elementos, titulo):
    styles = getSampleStyleSheet()

    estilo_titulo = ParagraphStyle(
        'TituloRelatorio',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor(COR_TEXTO),
        spaceAfter=6,
        spaceBefore=6,
        fontName='Helvetica-Bold',
        alignment=TA_LEFT
    )

    estilo_subtitulo = ParagraphStyle(
        'SubtituloRelatorio',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#64748b'),
        spaceAfter=12,
        fontName='Helvetica',
        alignment=TA_LEFT
    )

    elementos.append(Spacer(1, 0.3*cm))
    elementos.append(Paragraph(titulo, estilo_titulo))
    elementos.append(Paragraph(f"Emitido em: {date.today().strftime('%d/%m/%Y')}", estilo_subtitulo))

    linha = Table([['']], colWidths=[18*cm])
    linha.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 2, colors.HexColor(COR_AZUL)),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#e2e8f0')),
    ]))
    elementos.append(linha)
    elementos.append(Spacer(1, 0.5*cm))


def criar_rodape_pdf(elementos):
    styles = getSampleStyleSheet()

    estilo_rodape = ParagraphStyle(
        'RodapeRelatorio',
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
        estilo_rodape
    ))


def aplicar_estilo_tabela(table):
    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(COR_AZUL)),
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
        ])
    )
    return table


@relatorios_bp.route("/relatorios")
@login_required
@admin_required
def relatorios():
    hoje = date.today()

    proximos_vencimento = (
        Medicamento.query.filter(Medicamento.status_semaforo == 1)
        .order_by(Medicamento.data_validade)
        .all()
    )

    vencidos = (
        Medicamento.query.filter(Medicamento.status_semaforo == 2)
        .order_by(Medicamento.data_validade)
        .all()
    )

    total_medicos = Medico.query.count()
    total_farmacias = Farmacia.query.count()
    total_medicamentos = Medicamento.query.count()
    total_doacoes = Doacao.query.count()
    total_pacientes = Paciente.query.count()

    estatisticas_tarja = (
        db.session.query(
            Medicamento.tarja,
            func.count(Medicamento.id),
            func.sum(Medicamento.quantidade),
        )
        .group_by(Medicamento.tarja)
        .all()
    )

    return render_template(
        "relatorios.html",
        proximos_vencimento=proximos_vencimento,
        vencidos=vencidos,
        total_medicos=total_medicos,
        total_farmacias=total_farmacias,
        total_medicamentos=total_medicamentos,
        total_doacoes=total_doacoes,
        total_pacientes=total_pacientes,
        tarja_stats=estatisticas_tarja,
        hoje=hoje,
    )


def gerar_resposta_csv(nome_arquivo: str, cabecalhos: list, linhas_dados: list) -> Response:
    buffer = io.StringIO()
    escritor = csv.writer(buffer)
    escritor.writerow(cabecalhos)
    for linha in linhas_dados:
        escritor.writerow(linha)
    buffer.seek(0)
    return Response(
        "\ufeff" + buffer.getvalue(),
        mimetype="text/csv; charset=utf-8-sig",
        headers={"Content-Disposition": f'attachment; filename="{nome_arquivo}"'},
    )


@relatorios_bp.route("/relatorios/exportar/medicos")
@login_required
@equipe_clinica_required
def exportar_medicos():
    """Exporta lista de médicos para CSV"""
    lista_medicos = Medico.query.order_by(Medico.nome).all()
    registrar_log("Exportação CSV", "Exportou lista de médicos")

    linhas = [
        [
            medico.id,
            medico.nome,
            medico.crm,
            medico.especialidade,
            medico.contato or "",
            medico.created_at.strftime("%d/%m/%Y") if medico.created_at else "",
        ]
        for medico in lista_medicos
    ]

    return gerar_resposta_csv(
        f"medicos_{date.today()}.csv",
        ["ID", "Nome", "CRM", "Especialidade", "Contato", "Cadastrado em"],
        linhas,
    )


@relatorios_bp.route("/relatorios/exportar/farmacias")
@login_required
@equipe_clinica_required
def exportar_farmacias():
    """Exporta lista de farmácias para CSV"""
    lista_farmacias = Farmacia.query.order_by(Farmacia.nome_fantasia).all()
    registrar_log("Exportação CSV", "Exportou lista de farmácias")

    linhas = [
        [
            farmacia.id,
            farmacia.nome_fantasia,
            farmacia.razao_social or "",
            farmacia.cnpj,
            farmacia.responsavel,
            farmacia.endereco,
            farmacia.created_at.strftime("%d/%m/%Y") if farmacia.created_at else "",
        ]
        for farmacia in lista_farmacias
    ]

    return gerar_resposta_csv(
        f"farmacias_{date.today()}.csv",
        ["ID", "Nome Fantasia", "Razão Social", "CNPJ", "Responsável", "Endereço", "Cadastrado em"],
        linhas,
    )


@relatorios_bp.route("/relatorios/exportar/medicamentos")
@login_required
@equipe_clinica_required
def exportar_medicamentos():
    """Exporta lista de medicamentos para CSV"""
    lista_medicamentos = Medicamento.query.order_by(Medicamento.nome).all()
    registrar_log("Exportação CSV", "Exportou lista de medicamentos")

    mapa_status = {0: "Seguro", 1: "Próximo Vencimento", 2: "Vencido"}

    linhas = [
        [
            medicamento.id,
            medicamento.nome,
            medicamento.lote,
            medicamento.data_validade.strftime("%d/%m/%Y"),
            medicamento.quantidade,
            mapa_status.get(medicamento.status_semaforo, ""),
        ]
        for medicamento in lista_medicamentos
    ]

    return gerar_resposta_csv(
        f"medicamentos_{date.today()}.csv",
        ["ID", "Nome", "Lote", "Validade", "Quantidade", "Status"],
        linhas,
    )


@relatorios_bp.route("/relatorios/exportar/pacientes")
@login_required
@equipe_clinica_required
def exportar_pacientes():
    """Exporta lista de pacientes para CSV"""
    lista_pacientes = Paciente.query.order_by(Paciente.nome).all()
    registrar_log("Exportação CSV", "Exportou lista de pacientes")

    linhas = [
        [
            paciente.id,
            paciente.nome,
            paciente.cpf,
            paciente.data_nascimento.strftime("%d/%m/%Y") if paciente.data_nascimento else "",
            paciente.endereco or "",
            paciente.created_at.strftime("%d/%m/%Y") if paciente.created_at else "",
        ]
        for paciente in lista_pacientes
    ]

    return gerar_resposta_csv(
        f"pacientes_{date.today()}.csv",
        ["ID", "Nome", "CPF", "Data de Nascimento", "Endereço", "Cadastrado em"],
        linhas,
    )


@relatorios_bp.route("/relatorios/exportar/doacoes")
@login_required
@equipe_clinica_required
def exportar_doacoes():
    """Exporta histórico de doações para CSV"""
    lista_doacoes = Doacao.query.order_by(Doacao.data_doacao.desc()).all()
    registrar_log("Exportação CSV", "Exportou histórico de doações")

    linhas = [
        [
            doacao.id,
            doacao.data_doacao.strftime("%d/%m/%Y %H:%M"),
            doacao.medicamento.nome if doacao.medicamento else "—",
            doacao.medicamento.lote if doacao.medicamento else "—",
            doacao.quantidade,
            doacao.usuario.nome if doacao.usuario else "—",
            doacao.usuario.cargo if doacao.usuario else "—",
        ]
        for doacao in lista_doacoes
    ]

    return gerar_resposta_csv(
        f"doacoes_{date.today()}.csv",
        ["ID", "Data/Hora", "Medicamento", "Lote", "Qtd", "Responsável", "Cargo"],
        linhas,
    )


@relatorios_bp.route("/relatorios/exportar/medicamentos/pdf")
@login_required
@equipe_clinica_required
def exportar_medicamentos_pdf():
    """Exporta lista de medicamentos para PDF"""
    if not REPORTLAB_DISPONIVEL:
        return redirect(url_for("relatorios.relatorios"))

    lista_medicamentos = Medicamento.query.order_by(Medicamento.nome).all()
    registrar_log("Exportação PDF", "Exportou lista de medicamentos em PDF")

    resposta = Response(content_type="application/pdf")
    resposta.headers["Content-Disposition"] = (
        f"attachment; filename=medicamentos_{date.today()}.pdf"
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                           rightMargin=1.5*cm, leftMargin=1.5*cm,
                           topMargin=2*cm, bottomMargin=2*cm)
    elementos = []

    criar_cabecalho_pdf(elementos, "Relatório de Medicamentos")

    dados_tabela = [["Nome", "Lote", "Validade", "Qtd", "Status"]]
    mapa_status = {0: "Seguro", 1: "Próximo Vencimento", 2: "Vencido"}

    for medicamento in lista_medicamentos:
        dados_tabela.append([
            medicamento.nome,
            medicamento.lote,
            medicamento.data_validade.strftime("%d/%m/%Y") if hasattr(medicamento.data_validade, 'strftime') else str(medicamento.data_validade),
            str(medicamento.quantidade),
            mapa_status.get(medicamento.status_semaforo, ""),
        ])

    tabela = Table(dados_tabela, colWidths=[2.5 * inch, 1 * inch, 1 * inch, 0.5 * inch, 1.2 * inch])
    tabela = aplicar_estilo_tabela(tabela)
    elementos.append(tabela)

    criar_rodape_pdf(elementos)
    doc.build(elementos)

    pdf_bytes = buffer.getvalue()
    buffer.close()
    resposta.data = pdf_bytes

    return resposta


@relatorios_bp.route("/relatorios/exportar/medicos/pdf")
@login_required
@equipe_clinica_required
def exportar_medicos_pdf():
    """Exporta lista de médicos para PDF"""
    if not REPORTLAB_DISPONIVEL:
        return redirect(url_for("relatorios.relatorios"))

    lista_medicos = Medico.query.order_by(Medico.nome).all()
    registrar_log("Exportação PDF", "Exportou lista de médicos em PDF")

    resposta = Response(content_type="application/pdf")
    resposta.headers["Content-Disposition"] = (
        f"attachment; filename=medicos_{date.today()}.pdf"
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                           rightMargin=1.5*cm, leftMargin=1.5*cm,
                           topMargin=2*cm, bottomMargin=2*cm)
    elementos = []

    criar_cabecalho_pdf(elementos, "Relatório de Médicos")

    dados_tabela = [["Nome", "CRM", "Especialidade", "Contato", "Cadastrado em"]]

    for medico in lista_medicos:
        dados_tabela.append([
            medico.nome,
            medico.crm,
            medico.especialidade,
            medico.contato or "",
            medico.created_at.strftime("%d/%m/%Y") if medico.created_at else "",
        ])

    tabela = Table(dados_tabela, colWidths=[2 * inch, 1 * inch, 1.5 * inch, 1.5 * inch, 1 * inch])
    tabela = aplicar_estilo_tabela(tabela)
    elementos.append(tabela)

    criar_rodape_pdf(elementos)
    doc.build(elementos)

    pdf_bytes = buffer.getvalue()
    buffer.close()
    resposta.data = pdf_bytes

    return resposta


@relatorios_bp.route("/relatorios/exportar/farmacias/pdf")
@login_required
@equipe_clinica_required
def exportar_farmacias_pdf():
    """Exporta lista de farmácias para PDF"""
    if not REPORTLAB_DISPONIVEL:
        return redirect(url_for("relatorios.relatorios"))

    lista_farmacias = Farmacia.query.order_by(Farmacia.nome_fantasia).all()
    registrar_log("Exportação PDF", "Exportou lista de farmácias em PDF")

    resposta = Response(content_type="application/pdf")
    resposta.headers["Content-Disposition"] = (
        f"attachment; filename=farmacias_{date.today()}.pdf"
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                           rightMargin=1.5*cm, leftMargin=1.5*cm,
                           topMargin=2*cm, bottomMargin=2*cm)
    elementos = []

    criar_cabecalho_pdf(elementos, "Relatório de Farmácias")

    dados_tabela = [["Nome Fantasia", "Razão Social", "CNPJ", "Responsável", "Endereço", "Cadastrado em"]]

    for farmacia in lista_farmacias:
        dados_tabela.append([
            farmacia.nome_fantasia,
            farmacia.razao_social or "",
            farmacia.cnpj,
            farmacia.responsavel,
            farmacia.endereco,
            farmacia.created_at.strftime("%d/%m/%Y") if farmacia.created_at else "",
        ])

    tabela = Table(dados_tabela, colWidths=[1.5 * inch, 1.5 * inch, 1 * inch, 1 * inch, 1.5 * inch, 1 * inch])
    tabela = aplicar_estilo_tabela(tabela)
    elementos.append(tabela)

    criar_rodape_pdf(elementos)
    doc.build(elementos)

    pdf_bytes = buffer.getvalue()
    buffer.close()
    resposta.data = pdf_bytes

    return resposta


@relatorios_bp.route("/relatorios/exportar/pacientes/pdf")
@login_required
@equipe_clinica_required
def exportar_pacientes_pdf():
    """Exporta lista de pacientes para PDF"""
    if not REPORTLAB_DISPONIVEL:
        return redirect(url_for("relatorios.relatorios"))

    lista_pacientes = Paciente.query.order_by(Paciente.nome).all()
    registrar_log("Exportação PDF", "Exportou lista de pacientes em PDF")

    resposta = Response(content_type="application/pdf")
    resposta.headers["Content-Disposition"] = (
        f"attachment; filename=pacientes_{date.today()}.pdf"
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                           rightMargin=1.5*cm, leftMargin=1.5*cm,
                           topMargin=2*cm, bottomMargin=2*cm)
    elementos = []

    criar_cabecalho_pdf(elementos, "Relatório de Pacientes")

    dados_tabela = [["Nome", "CPF", "Data de Nascimento", "Endereço", "Cadastrado em"]]

    for paciente in lista_pacientes:
        dados_tabela.append([
            paciente.nome,
            paciente.cpf,
            paciente.data_nascimento.strftime("%d/%m/%Y") if paciente.data_nascimento else "",
            paciente.endereco or "",
            paciente.created_at.strftime("%d/%m/%Y") if paciente.created_at else "",
        ])

    tabela = Table(dados_tabela, colWidths=[2 * inch, 1 * inch, 1 * inch, 1.5 * inch, 1 * inch])
    tabela = aplicar_estilo_tabela(tabela)
    elementos.append(tabela)

    criar_rodape_pdf(elementos)
    doc.build(elementos)

    pdf_bytes = buffer.getvalue()
    buffer.close()
    resposta.data = pdf_bytes

    return resposta


@relatorios_bp.route("/relatorios/exportar/doacoes/pdf")
@login_required
@equipe_clinica_required
def exportar_doacoes_pdf():
    """Exporta histórico de doações para PDF"""
    if not REPORTLAB_DISPONIVEL:
        return redirect(url_for("relatorios.relatorios"))

    lista_doacoes = Doacao.query.order_by(Doacao.data_doacao.desc()).all()
    registrar_log("Exportação PDF", "Exportou histórico de doações em PDF")

    resposta = Response(content_type="application/pdf")
    resposta.headers["Content-Disposition"] = (
        f"attachment; filename=doacoes_{date.today()}.pdf"
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elementos = []

    styles = getSampleStyleSheet()
    titulo = Paragraph("Relatório de Doações", styles["Heading1"])
    elementos.append(titulo)

    dados_tabela = [["Data/Hora", "Medicamento", "Lote", "Qtd", "Responsável", "Cargo"]]

    for doacao in lista_doacoes:
        dados_tabela.append([
            doacao.data_doacao.strftime("%d/%m/%Y %H:%M"),
            doacao.medicamento.nome if doacao.medicamento else "—",
            doacao.medicamento.lote if doacao.medicamento else "—",
            str(doacao.quantidade),
            doacao.usuario.nome if doacao.usuario else "—",
            doacao.usuario.cargo if doacao.usuario else "—",
        ])

    tabela = Table(dados_tabela, colWidths=[1.2 * inch, 1.5 * inch, 0.8 * inch, 0.5 * inch, 1.2 * inch, 1 * inch])
    tabela.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 12),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ])
    )

    elementos.append(tabela)
    doc.build(elementos)

    pdf_bytes = buffer.getvalue()
    buffer.close()
    resposta.data = pdf_bytes

    return resposta


@relatorios_bp.route("/relatorios/exportar/sumario/pdf")
@login_required
@admin_required
def exportar_sumario_pdf():
    """Exporta sumário executivo com métricas do sistema"""
    if not REPORTLAB_DISPONIVEL:
        return redirect(url_for("relatorios.relatorios"))

    total_medicamentos = Medicamento.query.count()
    medicamentos_vencidos = Medicamento.query.filter(Medicamento.status_semaforo == 2).count()
    proximos_vencimento = Medicamento.query.filter(Medicamento.status_semaforo == 1).count()
    total_doacoes = Doacao.query.count()
    total_medicos = Medico.query.count()
    total_farmacias = Farmacia.query.count()
    total_pacientes = Paciente.query.count()

    resposta = Response(content_type="application/pdf")
    resposta.headers["Content-Disposition"] = (
        f"attachment; filename=sumario_redevita_{date.today()}.pdf"
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                           rightMargin=1.5*cm, leftMargin=1.5*cm,
                           topMargin=2*cm, bottomMargin=2*cm)
    elementos = []

    criar_cabecalho_pdf(elementos, "Sumário Executivo - RedeVita")

    styles = getSampleStyleSheet()
    estilo_resumo = ParagraphStyle(
        'Resumo',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor(COR_TEXTO),
        spaceAfter=12,
        leading=16
    )

    dados_resumo = [
        ["Métrica", "Quantidade", "Status"],
        ["Total de Medicamentos", str(total_medicamentos), "—" if total_medicamentos > 0 else "Vazio"],
        ["Medicamentos Vencidos", str(medicamentos_vencidos), "Crítico" if medicamentos_vencidos > 0 else "OK"],
        ["Próximos do Vencimento", str(proximos_vencimento), "Atenção" if proximos_vencimento > 0 else "OK"],
        ["Total de Doações", str(total_doacoes), "—" if total_doacoes > 0 else "Vazio"],
        ["Médicos Cadastrados", str(total_medicos), "—" if total_medicos > 0 else "Vazio"],
        ["Farmácias Parceiras", str(total_farmacias), "—" if total_farmacias > 0 else "Vazio"],
        ["Pacientes Cadastrados", str(total_pacientes), "—" if total_pacientes > 0 else "Vazio"],
    ]

    tabela_resumo = Table(dados_resumo, colWidths=[2.5 * inch, 1.5 * inch, 1.2 * inch])
    tabela_resumo = aplicar_estilo_tabela(tabela_resumo)
    elementos.append(tabela_resumo)

    elementos.append(Spacer(1, 0.5*cm))
    elementos.append(Paragraph("Observações:", styles['Heading3']))

    lista_observacoes = []
    if medicamentos_vencidos > 0:
        lista_observacoes.append(f"• {medicamentos_vencidos} medicamento(s) vencido(s). Ação: descarte imediato.")
    if proximos_vencimento > 0:
        lista_observacoes.append(f"• {proximos_vencimento} medicamento(s) próximo(s) do vencimento. Monitorar estoque.")
    if total_medicamentos == 0:
        lista_observacoes.append("• Nenhum medicamento cadastrado. Iniciar triagem de doações.")
    if total_doacoes == 0:
        lista_observacoes.append("• Nenhuma doação registrada. Sistema pronto para receber doações.")

    if not lista_observacoes:
        lista_observacoes.append("• Sistema operando dentro dos parâmetros normais.")

    for observacao in lista_observacoes:
        elementos.append(Paragraph(observacao, estilo_resumo))

    criar_rodape_pdf(elementos)
    doc.build(elementos)

    pdf_bytes = buffer.getvalue()
    buffer.close()
    resposta.data = pdf_bytes

    registrar_log("Exportação PDF", "Exportou sumário executivo em PDF")
    return resposta
