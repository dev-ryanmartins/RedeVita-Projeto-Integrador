from flask import Blueprint, render_template, request, jsonify, send_file
from flask_login import login_required, current_user
from app.models.medicamento import Medicamento
from app.models.doacao import Doacao
from app.models.paciente import Paciente
from app.models.farmacia import Farmacia
from app.database import db
from app.core.decorators import equipe_clinica_required
from app.core.api_responses import resposta_ok, resposta_erro
from app.utils.pdf_generator import obter_gerador_pdf
from datetime import date, datetime
from io import BytesIO
import logging
import os

logger = logging.getLogger(__name__)

impacto_bp = Blueprint("impacto", __name__)


@impacto_bp.route("/impacto")
@login_required
@equipe_clinica_required
def impacto_social():
    """Calcula e exibe métricas de impacto social e sustentabilidade"""
    
    # Cálculos de impacto
    total_medicamentos = Medicamento.query.count()
    total_doacoes = Doacao.query.count()
    total_pacientes = Paciente.query.count()
    total_farmacias = Farmacia.query.count()
    
    # Estimativas baseadas em dados reais
    total_estoque = sum(m.quantidade for m in Medicamento.query.all())
    
    # Cálculo de impacto (estimativas conservadoras)
    # 1 unidade de medicamento = ~1 paciente beneficiado
    pacientes_beneficiados = total_doacoes + total_estoque
    
    # Estimativa de resíduos evitados (1 unidade = ~50g de resíduo evitado)
    residuos_evitados_kg = (total_doacoes + total_estoque) * 0.05
    
    # Medicamentos salvos (total - vencidos)
    medicamentos_vencidos = Medicamento.query.filter_by(status_semaforo=2).count()
    medicamentos_salvos = total_medicamentos - medicamentos_vencidos
    
    # Métricas mensais
    hoje = date.today()
    doacoes_mes = Doacao.query.filter(
        Doacao.data_doacao >= date(hoje.year, hoje.month, 1)
    ).count()
    
    return render_template(
        "impacto.html",
        total_medicamentos=total_medicamentos,
        total_doacoes=total_doacoes,
        total_pacientes=total_pacientes,
        total_farmacias=total_farmacias,
        total_estoque=total_estoque,
        pacientes_beneficiados=pacientes_beneficiados,
        residuos_evitados_kg=round(residuos_evitados_kg, 2),
        medicamentos_salvos=medicamentos_salvos,
        medicamentos_vencidos=medicamentos_vencidos,
        doacoes_mes=doacoes_mes
    )


@impacto_bp.route("/api/impacto/exportar-pdf", methods=["POST"])
@login_required
@equipe_clinica_required
def exportar_pdf():
    """Exporta o relatório de impacto social em PDF"""
    try:
        data = request.get_json()
        
        if not data:
            return resposta_erro(
                mensagem="Corpo da requisição vazio",
                codigo=400
            )
        
        data_inicio = data.get("data_inicio")
        data_fim = data.get("data_fim")
        titulo = data.get("titulo", "Relatório de Impacto Social")
        observacoes = data.get("observacoes", "")
        dados_atuais = data.get("dados_atuais", {})
        graficos = data.get("graficos", {})
        
        # Escape de texto fornecido pelo usuário
        titulo = titulo.replace("<", "&lt;").replace(">", "&gt;")
        observacoes = observacoes.replace("<", "&lt;").replace(">", "&gt;")
        
        # Gerar PDF
        gerador = obter_gerador_pdf()
        pdf_bytes = gerador.gerar_pdf_impacto_social(
            data_inicio=data_inicio,
            data_fim=data_fim,
            titulo=titulo,
            observacoes=observacoes,
            dados=dados_atuais,
            graficos=graficos
        )
        
        # Criar nome do arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"relatorio_impacto_social_{timestamp}.pdf"
        
        # Enviar arquivo
        buffer = BytesIO(pdf_bytes)
        buffer.seek(0)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype="application/pdf"
        )
        
    except ImportError as e:
        logger.error(f"reportlab não instalado: {e}")
        return resposta_erro(
            mensagem="Biblioteca de PDF não instalada. Contate o administrador.",
            codigo=500
        )
    except Exception as e:
        logger.error(f"Erro ao exportar PDF: {e}")
        return resposta_erro(
            mensagem="Erro ao gerar PDF",
            codigo=500
        )
