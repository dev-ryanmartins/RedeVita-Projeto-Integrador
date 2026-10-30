"""
Blueprint para Janela de Resgate de Lotes.

Rota de planejamento para simular etapas hipotéticas e verificar margem
de tempo até a validade de lotes.

NOTA: Não faz alterações em dados reais. Apenas simulação.
"""

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.core.decorators import farmaceutico_required, admin_required
from app.core.api_responses import resposta_ok, resposta_erro
from app.services.lot_rescue_service import LotRescueService
import logging

logger = logging.getLogger(__name__)

lot_rescue_bp = Blueprint('lot_rescue', __name__)


@lot_rescue_bp.route('/janela-resgate-lotes', methods=['GET'])
@login_required
@farmaceutico_required
def janela_resgate():
    """
    Página principal da Janela de Resgate de Lotes.

    Acesso apenas para Admin e Farmacêutico.
    """
    return render_template('lot_rescue.html')


@lot_rescue_bp.route('/api/janela-resgate-lotes/lotes', methods=['GET'])
@login_required
@farmaceutico_required
def listar_lotes():
    """
    API para listar lotes com validade dentro do horizonte.

    Query params:
        horizon_dias: Horizonte em dias (1-365, default: 30)
        nome_medicamento: Filtro opcional por nome

    Returns:
        JSON com lista de lotes
    """
    try:
        horizon_dias = request.args.get('horizon_dias', 30, type=int)
        nome_medicamento = request.args.get('nome_medicamento', None, type=str)

        service = LotRescueService()
        lotes = service.listar_lotes_para_resgate(
            horizon_dias=horizon_dias,
            nome_medicamento=nome_medicamento
        )

        return resposta_ok(
            dados={
                'lotes': lotes,
                'total': len(lotes)
            },
            mensagem="Lotes listados com sucesso"
        )

    except ValueError as e:
        logger.warning(f"Parâmetro inválido: {e}")
        return resposta_erro(
            mensagem=str(e),
            codigo=400
        )
    except Exception as e:
        logger.error(f"Erro ao listar lotes: {e}")
        return resposta_erro(
            mensagem="Erro ao listar lotes",
            codigo=500
        )


@lot_rescue_bp.route('/api/janela-resgate-lotes/resumo', methods=['GET'])
@login_required
@farmaceutico_required
def resumo_lotes():
    """
    API para obter resumo estatístico de lotes.

    Query params:
        horizon_dias: Horizonte em dias (1-365, default: 30)
        nome_medicamento: Filtro opcional por nome

    Returns:
        JSON com resumo estatístico
    """
    try:
        horizon_dias = request.args.get('horizon_dias', 30, type=int)
        nome_medicamento = request.args.get('nome_medicamento', None, type=str)

        service = LotRescueService()
        resumo = service.calcular_resumo_lotes(
            horizon_dias=horizon_dias,
            nome_medicamento=nome_medicamento
        )

        return resposta_ok(
            dados=resumo,
            mensagem="Resumo calculado com sucesso"
        )

    except ValueError as e:
        logger.warning(f"Parâmetro inválido: {e}")
        return resposta_erro(
            mensagem=str(e),
            codigo=400
        )
    except Exception as e:
        logger.error(f"Erro ao calcular resumo: {e}")
        return resposta_erro(
            mensagem="Erro ao calcular resumo",
            codigo=500
        )


@lot_rescue_bp.route('/api/janela-resgate-lotes/simular', methods=['POST'])
@login_required
@farmaceutico_required
def simular_cenario():
    """
    API para simular um cenário de resgate.

    JSON body:
        lote_id: ID do lote
        etapas: Lista de etapas com 'nome' e 'duracao_dias'
        seed: Seed opcional para reprodutibilidade

    Returns:
        JSON com resultado da simulação
    """
    try:
        data = request.get_json()

        if not data:
            return resposta_erro(
                mensagem="Corpo da requisição vazio",
                codigo=400
            )

        lote_id = data.get('lote_id')
        etapas = data.get('etapas')
        seed = data.get('seed')

        if not lote_id:
            return resposta_erro(
                mensagem="lote_id é obrigatório",
                codigo=400
            )

        if not etapas or not isinstance(etapas, list):
            return resposta_erro(
                mensagem="etapas deve ser uma lista não vazia",
                codigo=400
            )

        service = LotRescueService()
        resultado = service.simular_cenario_resgate(
            lote_id=lote_id,
            etapas=etapas,
            seed=seed
        )

        return resposta_ok(
            dados=resultado,
            mensagem="Simulação executada com sucesso"
        )

    except ValueError as e:
        logger.warning(f"Parâmetro inválido: {e}")
        return resposta_erro(
            mensagem=str(e),
            codigo=400
        )
    except Exception as e:
        logger.error(f"Erro ao simular cenário: {e}")
        return resposta_erro(
            mensagem="Erro ao simular cenário",
            codigo=500
        )
