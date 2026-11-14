"""
QR Code Processing - Validação e Processamento de QR Codes
Permite baixa de estoque via escaneamento de QR Code criptografado.

As rotas atuam apenas como camada de transporte: validam o payload, delegam a
regra de negócio ao :class:`QRNonceService` e devolvem a resposta JSON.
"""

import logging

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user

from app.models.receita import Receita
from app.database import db
from app.core.decorators import farmaceutico_required
from app.extensions import limiter
from app.services.qr_nonce_service import QRNonceService

logger = logging.getLogger(__name__)

qrcode_bp = Blueprint("qrcode", __name__)

# Comprimento máximo aceitável para um nonce (token_hex(32) => 64 caracteres).
# Rejeitar entradas absurdamente longas evita abuso de memória/CPU na busca.
_NONCE_MAX_LEN = 128


@qrcode_bp.route("/api/qrcode/validate", methods=["POST"])
@limiter.limit("30 per minute")
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
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict) or not payload:
            return jsonify({"erro": "Dados do QR Code não fornecidos"}), 400

        nonce = payload.get("nonce", "")

        # Tipagem e limite de tamanho antes de qualquer consulta ao banco.
        if not isinstance(nonce, str) or not nonce.strip():
            return jsonify({"erro": "Nonce do QR Code não fornecido"}), 400

        nonce = nonce.strip()
        if len(nonce) > _NONCE_MAX_LEN:
            return jsonify({"erro": "Nonce do QR Code inválido"}), 400

        resultado = QRNonceService.dispensar_por_nonce(nonce, current_user.id)
        return jsonify(resultado.payload), resultado.status_http

    except Exception:
        db.session.rollback()
        logger.exception("Falha ao processar QR Code de prescrição")
        return jsonify({"erro": "Erro ao processar QR Code"}), 500


@qrcode_bp.route("/api/qrcode/generate/<int:receita_id>", methods=["GET"])
@limiter.limit("30 per minute")
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
        if not (
            current_user.cargo in ["Admin", "Farmacêutico", "Médico"]
            or (
                receita.paciente
                and hasattr(receita.paciente, "usuario_id")
                and receita.paciente.usuario_id == current_user.id
            )
        ):
            return jsonify({"erro": "Sem permissão para acessar esta receita"}), 403

        expiracao_minutos = current_app.config.get("QR_EXPIRATION_MINUTES", 15)
        qr_nonce = QRNonceService.gerar_nonce_para_receita(
            receita_id=receita_id,
            gerado_por_id=current_user.id,
            expiracao_minutos=expiracao_minutos,
        )

        # Return only nonce and expiration - no prescription ID to avoid clinical data exposure
        return jsonify({"nonce": qr_nonce.nonce, "expira_em": qr_nonce.expira_em.isoformat()}), 200

    except Exception:
        db.session.rollback()
        logger.exception("Falha ao gerar QR Code da prescrição")
        return jsonify({"erro": "Erro ao gerar QR Code"}), 500
