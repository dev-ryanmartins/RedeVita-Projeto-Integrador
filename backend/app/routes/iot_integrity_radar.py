"""
Blueprint para Radar de Integridade da Telemetria.

Área técnica para analisar telemetria IoT persistida e apontar padrões
que merecem conferência. Ferramenta de observabilidade, não prova de falha.

NOTA: Não faz alterações em dados reais. Apenas análise.
"""

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from app.core.decorators import admin_required
from app.core.api_responses import resposta_ok, resposta_erro
from app.services.iot_integrity_radar import IotIntegrityRadarService
import logging

logger = logging.getLogger(__name__)

iot_integrity_radar_bp = Blueprint('iot_integrity_radar', __name__)


@iot_integrity_radar_bp.route('/radar-integridade-telemetria', methods=['GET'])
@login_required
@admin_required
def radar_page():
    """
    Página principal do Radar de Integridade da Telemetria.

    Acesso apenas para Admin.
    """
    return render_template('iot_integrity_radar.html')


@iot_integrity_radar_bp.route('/api/radar-integridade-telemetria/resumo', methods=['GET'])
@login_required
@admin_required
def obter_resumo():
    """
    API para obter resumo dos sinais de integridade.

    Query params:
        periodo_dias: Período em dias (1-90, default: 7)

    Returns:
        JSON com resumo dos sinais
    """
    try:
        periodo_dias = request.args.get('periodo_dias', 7, type=int)

        service = IotIntegrityRadarService()
        resumo = service.obter_resumo(periodo_dias=periodo_dias)

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


@iot_integrity_radar_bp.route('/api/radar-integridade-telemetria/frescor', methods=['GET'])
@login_required
@admin_required
def analisar_frescor():
    """
    API para analisar frescor da telemetria por dispositivo.

    Query params:
        periodo_dias: Período em dias (1-90, default: 7)

    Returns:
        JSON com análise de frescor
    """
    try:
        periodo_dias = request.args.get('periodo_dias', 7, type=int)

        service = IotIntegrityRadarService()
        frescor = service.analisar_frescor(periodo_dias=periodo_dias)

        return resposta_ok(
            dados={
                'dispositivos': frescor,
                'total': len(frescor)
            },
            mensagem="Análise de frescor concluída"
        )

    except ValueError as e:
        logger.warning(f"Parâmetro inválido: {e}")
        return resposta_erro(
            mensagem=str(e),
            codigo=400
        )
    except Exception as e:
        logger.error(f"Erro ao analisar frescor: {e}")
        return resposta_erro(
            mensagem="Erro ao analisar frescor",
            codigo=500
        )


@iot_integrity_radar_bp.route('/api/radar-integridade-telemetria/lacunas', methods=['GET'])
@login_required
@admin_required
def analisar_lacunas():
    """
    API para analisar lacunas temporais na telemetria.

    Query params:
        intervalo_minutos: Intervalo esperado (ex: '1h', '6h', default: '1h')
        farmacia_id: Filtro opcional por farmácia
        dispositivo_id: Filtro opcional por dispositivo
        periodo_dias: Período em dias (1-90, default: 7)

    Returns:
        JSON com lacunas temporais detectadas
    """
    try:
        intervalo_minutos = request.args.get('intervalo_minutos', '1h')
        farmacia_id = request.args.get('farmacia_id', None, type=int)
        dispositivo_id = request.args.get('dispositivo_id', None, type=str)
        periodo_dias = request.args.get('periodo_dias', 7, type=int)

        service = IotIntegrityRadarService()
        lacunas = service.analisar_lacunas_temporais(
            intervalo_minutos=intervalo_minutos,
            farmacia_id=farmacia_id,
            dispositivo_id=dispositivo_id,
            periodo_dias=periodo_dias
        )

        return resposta_ok(
            dados={
                'lacunas': lacunas,
                'total': len(lacunas)
            },
            mensagem="Análise de lacunas concluída"
        )

    except ValueError as e:
        logger.warning(f"Parâmetro inválido: {e}")
        return resposta_erro(
            mensagem=str(e),
            codigo=400
        )
    except Exception as e:
        logger.error(f"Erro ao analisar lacunas: {e}")
        return resposta_erro(
            mensagem="Erro ao analisar lacunas",
            codigo=500
        )


@iot_integrity_radar_bp.route('/api/radar-integridade-telemetria/duplicidades', methods=['GET'])
@login_required
@admin_required
def analisar_duplicidades():
    """
    API para analisar candidatos a duplicidade.

    Query params:
        periodo_dias: Período em dias (1-90, default: 7)
        farmacia_id: Filtro opcional por farmácia
        dispositivo_id: Filtro opcional por dispositivo

    Returns:
        JSON com candidatos a duplicidade
    """
    try:
        periodo_dias = request.args.get('periodo_dias', 7, type=int)
        farmacia_id = request.args.get('farmacia_id', None, type=int)
        dispositivo_id = request.args.get('dispositivo_id', None, type=str)

        service = IotIntegrityRadarService()
        duplicidades = service.analisar_duplicidade_candidatos(
            periodo_dias=periodo_dias,
            farmacia_id=farmacia_id,
            dispositivo_id=dispositivo_id
        )

        return resposta_ok(
            dados={
                'duplicidades': duplicidades,
                'total': len(duplicidades)
            },
            mensagem="Análise de duplicidade concluída"
        )

    except ValueError as e:
        logger.warning(f"Parâmetro inválido: {e}")
        return resposta_erro(
            mensagem=str(e),
            codigo=400
        )
    except Exception as e:
        logger.error(f"Erro ao analisar duplicidades: {e}")
        return resposta_erro(
            mensagem="Erro ao analisar duplicidades",
            codigo=500
        )


@iot_integrity_radar_bp.route('/api/radar-integridade-telemetria/futuros', methods=['GET'])
@login_required
@admin_required
def analisar_futuros():
    """
    API para analisar timestamps no futuro.

    Query params:
        tolerancia_minutos: Tolerância em minutos (default: 60)
        periodo_dias: Período em dias (1-90, default: 7)
        farmacia_id: Filtro opcional por farmácia
        dispositivo_id: Filtro opcional por dispositivo

    Returns:
        JSON com leituras com timestamps no futuro
    """
    try:
        tolerancia_minutos = request.args.get('tolerancia_minutos', 60, type=int)
        periodo_dias = request.args.get('periodo_dias', 7, type=int)
        farmacia_id = request.args.get('farmacia_id', None, type=int)
        dispositivo_id = request.args.get('dispositivo_id', None, type=str)

        service = IotIntegrityRadarService()
        futuros = service.analisar_timestamps_futuros(
            tolerancia_minutos=tolerancia_minutos,
            periodo_dias=periodo_dias,
            farmacia_id=farmacia_id,
            dispositivo_id=dispositivo_id
        )

        return resposta_ok(
            dados={
                'futuros': futuros,
                'total': len(futuros)
            },
            mensagem="Análise de timestamps futuros concluída"
        )

    except ValueError as e:
        logger.warning(f"Parâmetro inválido: {e}")
        return resposta_erro(
            mensagem=str(e),
            codigo=400
        )
    except Exception as e:
        logger.error(f"Erro ao analisar timestamps futuros: {e}")
        return resposta_erro(
            mensagem="Erro ao analisar timestamps futuros",
            codigo=500
        )
