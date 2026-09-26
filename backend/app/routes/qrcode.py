"""
QR Code Processing - Validação e Processamento de QR Codes
Permite baixa de estoque via escaneamento de QR Code criptografado
"""

import json
import hashlib
import hmac
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app.models.receita import Receita
from app.models.medicamento import Medicamento
from app.database import db
from app.core.decorators import farmaceutico_required
from app.utils.log_helper import registrar_log

qrcode_bp = Blueprint("qrcode", __name__)


def _generate_qr_signature(data: dict, secret: str) -> str:
    """
    Gera assinatura HMAC-SHA256 para o QR Code.
    Garante integridade e autenticidade dos dados.
    """
    data_str = json.dumps(data, sort_keys=True)
    return hmac.new(
        secret.encode(),
        data_str.encode(),
        hashlib.sha256
    ).hexdigest()


def _verify_qr_signature(data: dict, signature: str, secret: str) -> bool:
    """
    Verifica a assinatura do QR Code.
    """
    expected = _generate_qr_signature(data, secret)
    return hmac.compare_digest(expected, signature)


@qrcode_bp.route("/api/qrcode/validate", methods=["POST"])
@login_required
@farmaceutico_required
def validate_qrcode():
    """
    Valida um QR Code escaneado e processa a baixa de estoque se válido.
    
    Expected JSON payload:
    {
        "data": { ...dados do QR Code... },
        "signature": "assinatura HMAC"
    }
    """
    try:
        from flask import current_app
        
        payload = request.get_json()
        if not payload:
            return jsonify({"erro": "Dados do QR Code não fornecidos"}), 400
        
        qr_data = payload.get("data", {})
        signature = payload.get("signature", "")
        
        # Verifica assinatura
        secret = current_app.config.get("SECRET_KEY", "default_secret")
        if not _verify_qr_signature(qr_data, signature, secret):
            return jsonify({"erro": "Assinatura do QR Code inválida"}), 400
        
        # Verifica tipo de QR Code
        qr_type = qr_data.get("type")
        
        if qr_type == "prescription":
            return _process_prescription_qrcode(qr_data)
        elif qr_type == "medication":
            return _process_medication_qrcode(qr_data)
        else:
            return jsonify({"erro": "Tipo de QR Code não suportado"}), 400
            
    except Exception as e:
        return jsonify({"erro": f"Erro ao processar QR Code: {str(e)}"}), 500


def _process_prescription_qrcode(qr_data: dict):
    """
    Processa QR Code de prescrição/receita.
    Realiza a baixa automática no estoque.
    """
    try:
        prescription_id = qr_data.get("id")
        
        if not prescription_id:
            return jsonify({"erro": "ID da prescrição não encontrado no QR Code"}), 400
        
        receita = Receita.query.get(prescription_id)
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
        
        # Verifica estoque
        if receita.medicamento.quantidade <= 0:
            return jsonify({"erro": "Medicamento sem estoque disponível"}), 400
        
        # Verifica se é controlado
        if receita.medicamento.controlado:
            if not receita.tipo_receita:
                return jsonify({
                    "erro": "Medicamento controlado requer tipo de receita especial"
                }), 400
        
        # Realiza baixa no estoque
        receita.status = "dispensada"
        receita.dispensada_em = datetime.utcnow()
        receita.dispensada_por_id = current_user.id
        receita.medicamento.quantidade -= 1
        
        db.session.commit()
        
        # Registra log
        if receita.medicamento.controlado:
            registrar_log(
                "Portaria 344 - Dispensação via QR Code",
                f'Receita CONTROLADA #{receita.id} dispensada via QR Code por {current_user.nome}'
            )
        else:
            registrar_log(
                "Dispensação via QR Code",
                f'Receita #{receita.id} dispensada via QR Code por {current_user.nome}'
            )
        
        return jsonify({
            "sucesso": True,
            "mensagem": f"Receita #{receita.id} dispensada com sucesso via QR Code",
            "medicamento": receita.medicamento.nome,
            "paciente": receita.paciente.nome if receita.paciente else "N/A",
            "estoque_restante": receita.medicamento.quantidade
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": f"Erro ao processar prescrição: {str(e)}"}), 500


def _process_medication_qrcode(qr_data: dict):
    """
    Processa QR Code de medicamento individual.
    Permite consulta rápida de informações.
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
    """
    try:
        from flask import current_app
        
        receita = Receita.query.get(receita_id)
        if not receita:
            return jsonify({"erro": "Receita não encontrada"}), 404
        
        # Verifica permissão
        if not (current_user.cargo in ["Admin", "Farmacêutico", "Médico"] or 
                (receita.paciente and hasattr(receita.paciente, 'usuario_id') and 
                 receita.paciente.usuario_id == current_user.id)):
            return jsonify({"erro": "Sem permissão para acessar esta receita"}), 403
        
        # Dados do QR Code
        qr_data = {
            "type": "prescription",
            "id": receita.id,
            "paciente": receita.paciente.nome if receita.paciente else "N/A",
            "medicamento": receita.medicamento.nome if receita.medicamento else "N/A",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Gera assinatura
        secret = current_app.config.get("SECRET_KEY", "default_secret")
        signature = _generate_qr_signature(qr_data, secret)
        
        return jsonify({
            "data": qr_data,
            "signature": signature,
            "receita_id": receita_id
        }), 200
        
    except Exception as e:
        return jsonify({"erro": f"Erro ao gerar QR Code: {str(e)}"}), 500
