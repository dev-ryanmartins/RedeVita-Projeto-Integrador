"""
QR Code Processing - Validação e Processamento de QR Codes
Permite baixa de estoque via escaneamento de QR Code criptografado
"""

import json
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app.models.receita import Receita
from app.models.medicamento import Medicamento
from app.models.qr_nonce import QRNonce
from app.database import db
from app.core.decorators import farmaceutico_required
from app.utils.log_helper import registrar_log

qrcode_bp = Blueprint("qrcode", __name__)


@qrcode_bp.route("/api/qrcode/validate", methods=["POST"])
@login_required
@farmaceutico_required
def validate_qrcode():
    """
    Valida um QR Code escaneado e processa a baixa de estoque se válido.
    
    Expected JSON payload:
    {
        "nonce": "token_opaco_aleatorio"
    }
    
    O nonce é persistido no servidor com expiração e rastreamento de uso.
    Assinatura HMAC não é usada pois o nonce está armazenado no banco
    e validado no servidor.
    """
    try:
        payload = request.get_json()
        if not payload:
            return jsonify({"erro": "Dados do QR Code não fornecidos"}), 400
        
        nonce = payload.get("nonce", "")
        
        if not nonce:
            return jsonify({"erro": "Nonce do QR Code não fornecido"}), 400
        
        # Processa validação e dispensação usando nonce
        return _process_prescription_qrcode_nonce(nonce)
            
    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": f"Erro ao processar QR Code: {str(e)}"}), 500


def _process_prescription_qrcode_nonce(nonce: str):
    """
    Processa QR Code de prescrição usando nonce opaco.
    Realiza a baixa automática no estoque de forma atômica.
    """
    try:
        # Lookup nonce in database
        qr_nonce = QRNonce.query.filter_by(nonce=nonce).first()
        
        if not qr_nonce:
            return jsonify({"erro": "QR Code inválido ou não encontrado"}), 404
        
        # Check if nonce is valid (not expired, not used)
        if not qr_nonce.is_valid():
            if qr_nonce.usado:
                return jsonify({
                    "erro": "QR Code já foi utilizado",
                    "ja_utilizado": True
                }), 400
            else:
                return jsonify({"erro": "QR Code expirado"}), 400
        
        # Get prescription from nonce
        receita = Receita.query.get(qr_nonce.receita_id)
        if not receita:
            return jsonify({"erro": "Receita não encontrada"}), 404
        
        # Verifica se já foi dispensada
        if receita.status == "dispensada":
            return jsonify({
                "sucesso": True,
                "mensagem": "Esta receita já foi dispensada anteriormente",
                "ja_dispensada": True
            }), 200
        
        # Verifica se há medicamento vinculado
        if not receita.medicamento:
            return jsonify({"erro": "Receita sem medicamento vinculado"}), 400
        
        # Verifica se é controlado
        if receita.medicamento.controlado:
            if not receita.tipo_receita:
                return jsonify({
                    "erro": "Medicamento controlado requer tipo de receita especial"
                }), 400
        
        # Use atomic stock reduction to prevent race conditions
        from app.utils.medication_validation import atomic_reduce_stock_quantity, validate_batch_for_stock_reduction
        
        # Validate expiration and quantity before attempting reduction
        validacao = validate_batch_for_stock_reduction(
            data_validade=receita.medicamento.data_validade,
            quantidade_solicitada=1,
            quantidade_disponivel=receita.medicamento.quantidade
        )
        
        if not validacao.is_valid:
            return jsonify({"erro": validacao.error_message}), 400
        
        # Atomically reduce stock
        success, new_quantity = atomic_reduce_stock_quantity(
            db.session,
            receita.medicamento_id,
            1
        )
        
        if not success:
            return jsonify({"erro": "Estoque insuficiente no momento da operação. Tente novamente."}), 400
        
        # Mark nonce as used and update prescription status in the same transaction
        qr_nonce.mark_as_used(current_user.id)
        
        receita.status = "dispensada"
        receita.dispensada_em = datetime.utcnow()
        receita.dispensada_por_id = current_user.id
        
        # Commit the entire transaction (nonce usage, stock reduction, prescription update)
        db.session.commit()
        
        # Registra log (without personal data)
        if receita.medicamento.controlado:
            registrar_log(
                "Portaria 344 - Dispensação via QR Code",
                f'Receita CONTROLADA #{receita.id} dispensada via QR Code por usuário #{current_user.id}'
            )
        else:
            registrar_log(
                "Dispensação via QR Code",
                f'Receita #{receita.id} dispensada via QR Code por usuário #{current_user.id}'
            )
        
        return jsonify({
            "sucesso": True,
            "mensagem": "Dispensação realizada com sucesso",
            "estoque_restante": new_quantity
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": f"Erro ao processar prescrição: {str(e)}"}), 500


def _process_medication_qrcode(qr_data: dict):
    """
    Processa QR Code de medicamento individual.
    Permite consulta rápida de informações.
    
    Nota: Este fluxo é apenas para consulta, não realiza baixa de estoque.
    Para dispensação de receitas, use o fluxo de prescrição com nonce.
    """
    try:
        medicamento_id = qr_data.get("id")
        
        if not medicamento_id:
            return jsonify({"erro": "ID do medicamento não encontrado no QR Code"}), 400
        
        medicamento = Medicamento.query.get(medicamento_id)
        if not medicamento:
            return jsonify({"erro": "Medicamento não encontrado"}), 404
        
        return jsonify({
            "sucesso": True,
            "medicamento": {
                "id": medicamento.id,
                "nome": medicamento.nome,
                "lote": medicamento.lote,
                "data_validade": medicamento.data_validade.strftime("%d/%m/%Y"),
                "quantidade": medicamento.quantidade,
                "tarja": medicamento.tarja,
                "principio_ativo": medicamento.principio_ativo,
                "controlado": medicamento.controlado
            }
        }), 200
        
    except Exception as e:
        return jsonify({"erro": f"Erro ao processar medicamento: {str(e)}"}), 500


@qrcode_bp.route("/api/qrcode/generate/<int:receita_id>", methods=["GET"])
@login_required
def generate_prescription_qrcode(receita_id):
    """
    Gera dados para QR Code de uma prescrição específica.
    Retorna JSON pronto para gerar o QR Code no frontend.
    
    O QR Code contém apenas um nonce opaco, sem dados pessoais ou clínicos.
    """
    try:
        receita = Receita.query.get(receita_id)
        if not receita:
            return jsonify({"erro": "Receita não encontrada"}), 404
        
        # Verifica permissão
        if not (current_user.cargo in ["Admin", "Farmacêutico", "Médico"] or 
                (receita.paciente and hasattr(receita.paciente, 'usuario_id') and 
                 receita.paciente.usuario_id == current_user.id)):
            return jsonify({"erro": "Sem permissão para acessar esta receita"}), 403
        
        # Create nonce for this prescription
        expiracao_minutos = current_app.config.get("QR_EXPIRATION_MINUTES", 15)
        qr_nonce = QRNonce.create_for_prescription(
            receita_id=receita_id,
            gerado_por_id=current_user.id,
            expiracao_minutos=expiracao_minutos
        )
        db.session.commit()
        
        # Return only nonce and expiration - no prescription ID to avoid clinical data exposure
        return jsonify({
            "nonce": qr_nonce.nonce,
            "expira_em": qr_nonce.expira_em.isoformat()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": f"Erro ao gerar QR Code: {str(e)}"}), 500
