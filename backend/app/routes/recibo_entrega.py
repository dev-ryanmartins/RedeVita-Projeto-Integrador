from flask import Blueprint, send_file, abort, current_app
from flask_login import login_required, current_user
from app.models.entrega_institucional import EntregaInstitucional, EstadoEntrega
from app.database import db
from app.utils.pdf_generator import gerar_recibo_entrega_async
from app.utils.log_helper import registrar_log
import os


recibo_entrega_bp = Blueprint("recibo_entrega", __name__, url_prefix="/recibo-entrega")


@recibo_entrega_bp.route("/<int:entrega_id>/pdf", methods=["GET"])
@login_required
def gerar_pdf_recibo(entrega_id):
    """
    Gera PDF de recibo de entrega institucional.
    
    Apenas entregas em estado RECEBIDA podem ter recibo gerado.
    """
    entrega = db.session.get(EntregaInstitucional, entrega_id)
    if not entrega:
        abort(404, "Entrega não encontrada")
    
    # Verifica se a entrega está em estado RECEBIDA
    if entrega.estado != EstadoEntrega.RECEBIDA.value:
        abort(400, f"Recibo só pode ser gerado para entregas recebidas. Estado atual: {entrega.estado}")
    
    # Verifica autorização: usuário da instituição destinatária ou admin
    instituicao_destino = entrega.reserva.instituicao_id
    if not current_user.is_admin and current_user.instituicao_id != instituicao_destino:
        abort(403, "Você não tem permissão para acessar este recibo")
    
    try:
        # Coleta dados para o recibo
        dados_entrega = {
            'entrega_id': entrega.id,
            'reserva_id': entrega.reserva_id,
            'farmacia_origem': entrega.reserva.oferta.farmacia.nome_fantasia if entrega.reserva.oferta.farmacia else 'N/A',
            'cnpj_origem': entrega.reserva.oferta.farmacia.cnpj if entrega.reserva.oferta.farmacia else 'N/A',
            'instituicao_destino': entrega.reserva.instituicao.nome if entrega.reserva.instituicao else 'N/A',
            'cnpj_destino': entrega.reserva.instituicao.cnpj if entrega.reserva.instituicao else 'N/A',
            'medicamento_nome': entrega.reserva.oferta.medicamento.nome if entrega.reserva.oferta.medicamento else 'N/A',
            'medicamento_lote': entrega.reserva.oferta.medicamento.lote if entrega.reserva.oferta.medicamento else 'N/A',
            'medicamento_validade': entrega.reserva.oferta.medicamento.data_validade if entrega.reserva.oferta.medicamento else None,
            'quantidade': entrega.reserva.quantidade_reservada,
            'recebido_por': entrega.recebido_por.nome if entrega.recebido_por else 'N/A',
            'recebido_em': entrega.recebido_em,
            'observacoes': entrega.observacoes
        }
        
        # Gera PDF
        from app.utils.pdf_generator import PDFGenerator
        gerador = PDFGenerator()
        pdf_bytes = gerador.gerar_recibo_entrega(dados_entrega)
        
        if not pdf_bytes:
            abort(500, "Erro ao gerar PDF")
        
        # Registrar log
        registrar_log(
            "Geração Recibo Entrega",
            f'Recibo gerado para entrega {entrega.id} por usuário {current_user.id}',
        )
        
        # Envia PDF como response
        return send_file(
            path_or_file=pdf_bytes,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'recibo_entrega_{entrega.id}.pdf'
        )
        
    except Exception as e:
        current_app.logger.error(f"Erro ao gerar recibo: {str(e)}")
        abort(500, "Erro ao gerar recibo")
