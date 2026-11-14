"""
Serviço de dispensação de receitas via QR Nonce.

Concentra a regra de negócio de validação/consumo de um *nonce* de QR Code e a
baixa atômica de estoque, mantendo as rotas enxutas (receber requisição →
chamar serviço → devolver resposta).

O nonce é opaco, de uso único, armazenado no servidor com expiração e consumido
de forma atômica junto com a baixa de estoque e a atualização do status da
receita, evitando condições de corrida.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict

from app.models.receita import Receita
from app.models.qr_nonce import QRNonce
from app.database import db
from app.utils.log_helper import registrar_log
from app.utils.medication_validation import (
    atomic_reduce_stock_quantity,
    validate_batch_for_stock_reduction,
)

logger = logging.getLogger(__name__)


@dataclass
class ResultadoDispensacao:
    """Resultado da tentativa de dispensação via QR Nonce.

    Attributes:
        payload: Corpo JSON a ser retornado ao cliente.
        status_http: Código HTTP da resposta.
    """

    payload: Dict[str, Any]
    status_http: int


class QRNonceService:
    """Serviço responsável pela geração e consumo de QR Nonces."""

    @staticmethod
    def gerar_nonce_para_receita(
        receita_id: int,
        gerado_por_id: int,
        expiracao_minutos: int = 15,
    ) -> QRNonce:
        """Cria e persiste um novo nonce de QR Code para uma receita.

        Args:
            receita_id: Identificador da receita associada.
            gerado_por_id: Identificador do usuário que gerou o nonce.
            expiracao_minutos: Tempo de validade do nonce, em minutos.

        Returns:
            A instância :class:`QRNonce` criada e já confirmada no banco.
        """
        qr_nonce = QRNonce.create_for_prescription(
            receita_id=receita_id,
            gerado_por_id=gerado_por_id,
            expiracao_minutos=expiracao_minutos,
        )
        db.session.commit()

        logger.info("QR Nonce gerado: receita=%s usuario=%s", receita_id, gerado_por_id)
        return qr_nonce

    @staticmethod
    def dispensar_por_nonce(nonce: str, usuario_id: int) -> ResultadoDispensacao:
        """Valida um nonce e executa a dispensação atômica da receita.

        O fluxo verifica existência/validade do nonce, vínculo com a receita,
        restrições sanitárias (Portaria 344) e disponibilidade de estoque. A
        baixa de estoque, o consumo do nonce e a atualização da receita ocorrem
        em uma única transação.

        Args:
            nonce: Token opaco lido do QR Code.
            usuario_id: Identificador do usuário (farmacêutico) que dispensa.

        Returns:
            :class:`ResultadoDispensacao` com o payload e o status HTTP.
        """
        qr_nonce = QRNonce.query.filter_by(nonce=nonce).first()

        if not qr_nonce:
            return ResultadoDispensacao({"erro": "QR Code inválido ou não encontrado"}, 404)

        if not qr_nonce.is_valid():
            if qr_nonce.usado:
                return ResultadoDispensacao({"erro": "QR Code já foi utilizado", "ja_utilizado": True}, 400)
            return ResultadoDispensacao({"erro": "QR Code expirado"}, 400)

        receita = Receita.query.get(qr_nonce.receita_id)
        if not receita:
            return ResultadoDispensacao({"erro": "Receita não encontrada"}, 404)

        if receita.status == "dispensada":
            return ResultadoDispensacao(
                {
                    "sucesso": True,
                    "mensagem": "Esta receita já foi dispensada anteriormente",
                    "ja_dispensada": True,
                },
                200,
            )

        if not receita.medicamento:
            return ResultadoDispensacao({"erro": "Receita sem medicamento vinculado"}, 400)

        if receita.medicamento.controlado and not receita.tipo_receita:
            return ResultadoDispensacao(
                {"erro": "Medicamento controlado requer tipo de receita especial"},
                400,
            )

        validacao = validate_batch_for_stock_reduction(
            data_validade=receita.medicamento.data_validade,
            quantidade_solicitada=1,
            quantidade_disponivel=receita.medicamento.quantidade,
        )
        if not validacao.is_valid:
            return ResultadoDispensacao({"erro": validacao.error_message}, 400)

        success, nova_quantidade = atomic_reduce_stock_quantity(db.session, receita.medicamento_id, 1)
        if not success:
            return ResultadoDispensacao(
                {"erro": "Estoque insuficiente no momento da operação. Tente novamente."},
                400,
            )

        # Consumo do nonce + status da receita na mesma transação da baixa de estoque.
        qr_nonce.mark_as_used(usuario_id)
        receita.status = "dispensada"
        receita.dispensada_em = datetime.utcnow()
        receita.dispensada_por_id = usuario_id
        db.session.commit()

        QRNonceService._registrar_auditoria(receita, usuario_id)

        logger.info(
            "QR Nonce consumido: receita=%s usuario=%s estoque_restante=%s",
            receita.id,
            usuario_id,
            nova_quantidade,
        )
        return ResultadoDispensacao(
            {
                "sucesso": True,
                "mensagem": "Dispensação realizada com sucesso",
                "estoque_restante": nova_quantidade,
            },
            200,
        )

    @staticmethod
    def _registrar_auditoria(receita: Receita, usuario_id: int) -> None:
        """Registra o evento de dispensação (sem dados pessoais) no log de auditoria."""
        if receita.medicamento and receita.medicamento.controlado:
            registrar_log(
                "Portaria 344 - Dispensação via QR Code",
                f"Receita CONTROLADA #{receita.id} dispensada via QR Code por usuário #{usuario_id}",
            )
        else:
            registrar_log(
                "Dispensação via QR Code",
                f"Receita #{receita.id} dispensada via QR Code por usuário #{usuario_id}",
            )
