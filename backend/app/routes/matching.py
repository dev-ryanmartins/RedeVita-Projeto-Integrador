from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.services.matching_service import MatchingService
from app.models.oferta_medicamento import OfertaMedicamento
from app.models.necessidade_institucional import NecessidadeInstitucional
from app.models.reserva_oferta import ReservaOferta, StatusReserva
from app.models.instituicao import Instituicao
from app.database import db
from app.core.decorators import admin_required
from app.utils.log_helper import registrar_log
from app.utils.sanitize import limpar
from app.models.movimento_estoque import MovimentoEstoque


matching_bp = Blueprint("matching", __name__, url_prefix="/matching")


@matching_bp.route("/")
@login_required
def dashboard_matching():
    """Dashboard de matching entre ofertas e necessidades."""
    # Admin vê todas as necessidades
    if current_user.is_admin:
        necessidades = NecessidadeInstitucional.query.order_by(NecessidadeInstitucional.prioridade.desc()).all()
    else:
        # Usuário institucional vê apenas necessidades da sua instituição
        if current_user.instituicao_id:
            necessidades = NecessidadeInstitucional.query.filter_by(
                instituicao_id=current_user.instituicao_id
            ).order_by(NecessidadeInstitucional.prioridade.desc()).all()
        else:
            necessidades = []
    
    return render_template("matching_dashboard.html", necessidades=necessidades)


@matching_bp.route("/api/sugerir_para_necessidade/<int:necessidade_id>")
@login_required
def api_sugerir_para_necessidade(necessidade_id):
    """API para buscar matches para uma necessidade específica."""
    # Verifica autorização: usuário vinculado à instituição da necessidade ou admin
    necessidade = db.session.get(NecessidadeInstitucional, necessidade_id)
    if not necessidade:
        return jsonify({"error": "Necessidade não encontrada"}), 404
    
    if not current_user.is_admin and current_user.instituicao_id != necessidade.instituicao_id:
        return jsonify({"error": "Você não tem permissão para acessar esta necessidade"}), 403
    
    matches = MatchingService.buscar_matches_para_necessidade(necessidade_id, limite=5)
    
    resultados = []
    for match in matches:
        resultados.append({
            "oferta_id": match.oferta.id,
            "medicamento": match.oferta.medicamento.nome if match.oferta.medicamento else "N/A",
            "farmacia": match.oferta.farmacia.nome_fantasia if match.oferta.farmacia else "N/A",
            "quantidade_disponivel": match.oferta.quantidade_disponivel,
            "compativel": match.compativel,
            "motivo": match.motivo
        })
    
    return jsonify({"matches": resultados})


@matching_bp.route("/api/sugerir_para_oferta/<int:oferta_id>")
@login_required
def api_sugerir_para_oferta(oferta_id):
    """API para buscar matches para uma oferta específica."""
    # Verifica autorização: usuário vinculado à farmácia da oferta ou admin
    oferta = db.session.get(OfertaMedicamento, oferta_id)
    if not oferta:
        return jsonify({"error": "Oferta não encontrada"}), 404
    
    if not current_user.is_admin and current_user.farmacia_id != oferta.farmacia_id:
        return jsonify({"error": "Você não tem permissão para acessar esta oferta"}), 403
    
    matches = MatchingService.buscar_matches_para_oferta(oferta_id, limite=5)
    
    resultados = []
    for match in matches:
        resultados.append({
            "necessidade_id": match.necessidade.id,
            "instituicao": match.necessidade.instituicao.nome if match.necessidade.instituicao else match.necessidade.nome_instituicao,
            "produto": match.necessidade.produto_descritivo or "N/A",
            "quantidade_solicitada": match.necessidade.quantidade_solicitada,
            "prioridade": match.necessidade.prioridade,
            "compativel": match.compativel,
            "motivo": match.motivo
        })
    
    return jsonify({"matches": resultados})


@matching_bp.route("/api/verificar_compatibilidade", methods=["POST"])
@login_required
def api_verificar_compatibilidade():
    """API para verificar compatibilidade entre oferta e necessidade."""
    oferta_id = request.json.get("oferta_id", type=int)
    necessidade_id = request.json.get("necessidade_id", type=int)
    
    if not oferta_id or not necessidade_id:
        return jsonify({"error": "oferta_id e necessidade_id são obrigatórios"}), 400
    
    # Verifica autorização: usuário vinculado à instituição da necessidade ou farmácia da oferta
    necessidade = db.session.get(NecessidadeInstitucional, necessidade_id)
    oferta = db.session.get(OfertaMedicamento, oferta_id)
    
    if not necessidade or not oferta:
        return jsonify({"error": "Oferta ou necessidade não encontrada"}), 404
    
    if not current_user.is_admin:
        # Usuário deve estar vinculado à instituição da necessidade ou à farmácia da oferta
        if (current_user.instituicao_id != necessidade.instituicao_id and 
            current_user.farmacia_id != oferta.farmacia_id):
            return jsonify({"error": "Você não tem permissão para verificar esta compatibilidade"}), 403
    
    sugestao = MatchingService.sugerir_reserva(oferta_id, necessidade_id)
    
    return jsonify(sugestao)


@matching_bp.route("/criar_reserva_via_matching", methods=["POST"])
@login_required
def criar_reserva_via_matching():
    """Cria uma reserva a partir de uma sugestão de matching."""
    oferta_id = request.json.get("oferta_id", type=int)
    necessidade_id = request.json.get("necessidade_id", type=int)
    quantidade = request.json.get("quantidade", type=int)
    
    if not oferta_id or not necessidade_id or not quantidade:
        return jsonify({"error": "oferta_id, necessidade_id e quantidade são obrigatórios"}), 400
    
    # Verifica compatibilidade
    sugestao = MatchingService.sugerir_reserva(oferta_id, necessidade_id)
    if not sugestao.get("compativel"):
        return jsonify({"error": sugestao.get("motivo", "Incompatível")}), 400
    
    # Busca a instituição da necessidade
    necessidade = db.session.get(NecessidadeInstitucional, necessidade_id)
    if not necessidade or not necessidade.instituicao_id:
        return jsonify({"error": "Necessidade não tem instituição vinculada"}), 400
    
    # Cria a reserva
    operacao_id = MovimentoEstoque.gerar_operacao_id()
    
    try:
        reserva = ReservaOferta(
            oferta_id=oferta_id,
            instituicao_id=necessidade.instituicao_id,
            quantidade_reservada=quantidade,
            status=StatusReserva.RESERVADA.value,
            reservado_por_id=current_user.id,
            operacao_id=operacao_id
        )
        db.session.add(reserva)
        
        # Reserva a quantidade na oferta de forma atômica
        success, nova_quantidade = OfertaMedicamento.reservar_atomico(
            db.session,
            oferta_id,
            quantidade
        )
        
        if not success:
            db.session.rollback()
            return jsonify({"error": "Erro ao reservar quantidade na oferta. Disponibilidade insuficiente."}), 400
        
        db.session.commit()
        registrar_log(
            "Reserva via Matching",
            f'Reserva criada via matching: oferta {oferta_id} para necessidade {necessidade_id}',
        )
        
        return jsonify({
            "success": True,
            "reserva_id": reserva.id,
            "mensagem": f"Reserva de {quantidade} unidades criada com sucesso"
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erro ao criar reserva: {str(e)}"}), 500
