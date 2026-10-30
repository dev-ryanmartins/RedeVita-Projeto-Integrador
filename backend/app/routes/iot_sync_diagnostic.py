"""
IoT Sync Diagnostic - Blueprint para diagnóstico de sincronização IoT
Área administrativa para acompanhar lotes de telemetria recebidos pela API
"""
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify
from sqlalchemy import or_, and_

from app.core.decorators import admin_required
from app.core.api_responses import resposta_ok, resposta_erro, ERRO_VALIDACAO
from app.database import db
from app.models.iot import LoteTelemetria, ResultadoLoteEnum

iot_sync_diagnostic_bp = Blueprint('iot_sync_diagnostic', __name__)


MAX_PAGE_SIZE = 50
DEFAULT_PAGE_SIZE = 20
MAX_INTERVAL_DAYS = 90


@iot_sync_diagnostic_bp.route('/admin/diagnostico-iot')
@admin_required
def diagnostico_iot_page():
    """Página administrativa para diagnóstico de sincronização IoT"""
    return render_template('iot_sync_diagnostic.html')


@iot_sync_diagnostic_bp.route('/api/admin/diagnostico-iot/dados')
@admin_required
def diagnostico_iot_dados():
    """Endpoint JSON para dados de diagnóstico de sincronização IoT"""
    try:
        # Extrair e validar parâmetros
        page = max(1, int(request.args.get('page', 1)))
        page_size = min(MAX_PAGE_SIZE, max(1, int(request.args.get('page_size', DEFAULT_PAGE_SIZE))))
        
        # Filtro de período
        data_inicio_str = request.args.get('data_inicio')
        data_fim_str = request.args.get('data_fim')
        
        # Filtro de resultado
        resultado_filtro = request.args.get('resultado')
        
        # Filtro de dispositivo
        dispositivo_filtro = request.args.get('dispositivo')
        
        # Validação de datas
        if data_inicio_str:
            try:
                data_inicio = datetime.fromisoformat(data_inicio_str)
            except ValueError:
                return resposta_erro(ERRO_VALIDACAO, "Formato de data início inválido. Use ISO-8601 (YYYY-MM-DD)", 400)
        else:
            data_inicio = datetime.utcnow() - timedelta(days=7)
        
        if data_fim_str:
            try:
                data_fim = datetime.fromisoformat(data_fim_str)
            except ValueError:
                return resposta_erro(ERRO_VALIDACAO, "Formato de data fim inválido. Use ISO-8601 (YYYY-MM-DD)", 400)
        else:
            data_fim = datetime.utcnow()
        
        # Validar intervalo máximo
        if (data_fim - data_inicio).days > MAX_INTERVAL_DAYS:
            return resposta_erro(
                ERRO_VALIDACAO,
                f"Intervalo máximo permitido é de {MAX_INTERVAL_DAYS} dias",
                400
            )
        
        # Construir query base
        query = LoteTelemetria.query.filter(
            LoteTelemetria.data_recebimento >= data_inicio,
            LoteTelemetria.data_recebimento <= data_fim
        )
        
        # Aplicar filtro de resultado
        if resultado_filtro:
            try:
                resultado_enum = ResultadoLoteEnum(resultado_filtro)
                query = query.filter(LoteTelemetria.resultado == resultado_enum)
            except ValueError:
                return resposta_erro(ERRO_VALIDACAO, "Valor de resultado inválido", 400)
        
        # Aplicar filtro de dispositivo (apenas se único dispositivo no lote)
        if dispositivo_filtro:
            query = query.filter(LoteTelemetria.dispositivo_principal == dispositivo_filtro)
        
        # Ordenar por data decrescente
        query = query.order_by(LoteTelemetria.data_recebimento.desc())
        
        # Paginar
        paginated = query.paginate(page=page, per_page=page_size, error_out=False)
        
        # Serializar lotes
        lotes = []
        for lote in paginated.items:
            lotes.append({
                'id': lote.id,
                'lote_id': lote.lote_id,
                'data_recebimento': lote.data_recebimento.isoformat() if lote.data_recebimento else None,
                'total_recebidas': lote.total_recebidas,
                'total_processadas': lote.total_processadas,
                'total_rejeitadas': lote.total_rejeitadas,
                'resultado': lote.resultado.value,
                'qtd_dispositivos': lote.qtd_dispositivos,
                'dispositivo_principal': lote.dispositivo_principal,
                'erros_por_categoria': lote.erros_por_categoria
            })
        
        # Calcular agregados para o período filtrado
        total_lotes = paginated.total
        total_recebidas_periodo = sum(l.total_recebidas for l in paginated.items)
        total_processadas_periodo = sum(l.total_processadas for l in paginated.items)
        total_rejeitadas_periodo = sum(l.total_rejeitadas for l in paginated.items)
        
        contagem_por_resultado = {}
        for lote in paginated.items:
            resultado = lote.resultado.value
            contagem_por_resultado[resultado] = contagem_por_resultado.get(resultado, 0) + 1
        
        return resposta_ok({
            'status': 'ok',
            'lotes': lotes,
            'paginacao': {
                'page': page,
                'page_size': page_size,
                'total': paginated.total,
                'pages': paginated.pages,
                'has_next': paginated.has_next,
                'has_prev': paginated.has_prev
            },
            'agregados': {
                'total_lotes': total_lotes,
                'total_recebidas': total_recebidas_periodo,
                'total_processadas': total_processadas_periodo,
                'total_rejeitadas': total_rejeitadas_periodo,
                'contagem_por_resultado': contagem_por_resultado
            },
            'filtros_aplicados': {
                'data_inicio': data_inicio.isoformat(),
                'data_fim': data_fim.isoformat(),
                'resultado': resultado_filtro,
                'dispositivo': dispositivo_filtro
            }
        })
        
    except Exception as e:
        return resposta_erro(f"Erro ao buscar dados de diagnóstico: {str(e)}", 500)


@iot_sync_diagnostic_bp.route('/api/admin/diagnostico-iot/dispositivos')
@admin_required
def listar_dispositivos():
    """Endpoint para listar dispositivos disponíveis para filtro"""
    try:
        # Buscar dispositivos que aparecem como principal em lotes
        dispositivos = db.session.query(
            LoteTelemetria.dispositivo_principal
        ).filter(
            LoteTelemetria.dispositivo_principal.isnot(None)
        ).distinct().all()
        
        lista_dispositivos = [d[0] for d in dispositivos if d[0]]
        
        return resposta_ok({
            'dispositivos': sorted(lista_dispositivos)
        })
        
    except Exception as e:
        return resposta_erro(f"Erro ao listar dispositivos: {str(e)}", 500)
