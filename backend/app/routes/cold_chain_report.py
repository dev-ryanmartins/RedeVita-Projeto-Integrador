"""
Relatório da Cadeia de Frio - Cold Chain Report

Acesso exclusivo para administradores para consultar histórico real
de telemetria IoT persistida, com filtros, indicadores agregados e exportação CSV.
"""

from flask import Blueprint, render_template, jsonify, request, Response
from flask_login import login_required
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
import csv
import io

from app.core.decorators import admin_required
from app.database import db
from app.models.iot import LeituraIoT, StatusAlertaEnum

cold_chain_report_bp = Blueprint('cold_chain_report', __name__)

# Limites
MAX_INTERVAL_DAYS = 90  # Limite máximo de intervalo em dias
MAX_ITEMS_PER_PAGE = 100  # Limite máximo de itens por página
DEFAULT_ITEMS_PER_PAGE = 20  # Padrão de itens por página
MAX_EXPORT_ROWS = 10000  # Limite máximo de linhas exportáveis


@cold_chain_report_bp.route('/admin/relatorio-cadeia-frio')
@login_required
@admin_required
def relatorio_cadeia_frio():
    """
    Página do Relatório da Cadeia de Frio (UI).
    Acessível apenas por administradores.
    """
    return render_template('cold_chain_report.html',
                          max_interval_days=MAX_INTERVAL_DAYS,
                          default_items_per_page=DEFAULT_ITEMS_PER_PAGE)


@cold_chain_report_bp.route('/api/admin/relatorio-cadeia-frio/dados')
@login_required
@admin_required
def relatorio_cadeia_frio_dados():
    """
    Endpoint JSON para dados do Relatório da Cadeia de Frio.
    Acessível apenas por administradores.
    
    Retorna indicadores agregados e leituras paginadas.
    """
    try:
        # Obter e validar filtros
        filters = _get_and_validate_filters(request.args)
        
        if 'error' in filters:
            return jsonify({
                'status': 'error',
                'message': filters['error']
            }), 400
        
        # Calcular indicadores agregados
        indicators = _calculate_indicators(filters)
        
        # Obter leituras paginadas
        page = request.args.get('page', 1, type=int)
        per_page = min(
            request.args.get('per_page', DEFAULT_ITEMS_PER_PAGE, type=int),
            MAX_ITEMS_PER_PAGE
        )
        
        readings = _get_paginated_readings(filters, page, per_page)
        
        return jsonify({
            'status': 'ok',
            'timestamp': datetime.utcnow().isoformat(),
            'indicators': indicators,
            'readings': readings,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': indicators['total_leituras']
            }
        }), 200
        
    except Exception as e:
        # Log sanitizado
        from app.utils.log_helper import registrar_log
        registrar_log("RelatorioCadeiaFrio", f"Erro ao obter dados: {str(e)}")
        
        return jsonify({
            'status': 'error',
            'message': 'Erro ao carregar dados do relatório'
        }), 500


@cold_chain_report_bp.route('/api/admin/relatorio-cadeia-frio/exportar-csv')
@login_required
@admin_required
def relatorio_cadeia_frio_exportar_csv():
    """
    Endpoint para exportação CSV do Relatório da Cadeia de Frio.
    Acessível apenas por administradores.
    
    Usa os mesmos filtros da consulta e protege contra CSV injection.
    """
    try:
        # Obter e validar filtros
        filters = _get_and_validate_filters(request.args)
        
        if 'error' in filters:
            return jsonify({
                'status': 'error',
                'message': filters['error']
            }), 400
        
        # Obter leituras com limite de exportação
        readings = _get_readings_for_export(filters)
        
        if len(readings) > MAX_EXPORT_ROWS:
            return jsonify({
                'status': 'error',
                'message': f'O limite de exportação é de {MAX_EXPORT_ROWS} linhas. Refine os filtros.'
            }), 400
        
        # Criar CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Cabeçalho
        writer.writerow([
            'Data/Hora',
            'Dispositivo',
            'Farmacia ID',
            'Temperatura (°C)',
            'Umidade (%)',
            'Luminosidade (lux)',
            'Status Alerta'
        ])
        
        # Linhas (sanitizadas contra CSV injection)
        for reading in readings:
            # Sanitizar campos que podem conter fórmulas CSV
            device_id = _sanitize_csv_field(reading.dispositivo_id)
            status = _sanitize_csv_field(reading.status_alerta.value)
            
            writer.writerow([
                reading.data_hora.isoformat() if reading.data_hora else '',
                device_id,
                reading.farmacia_id,
                reading.temperatura,
                reading.umidade,
                reading.luminosidade_lux,
                status
            ])
        
        # Criar resposta
        output.seek(0)
        response = Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': 'attachment; filename=relatorio_cadeia_frio.csv',
                'Content-Type': 'text/csv; charset=utf-8'
            }
        )
        
        return response
        
    except Exception as e:
        # Log sanitizado
        from app.utils.log_helper import registrar_log
        registrar_log("RelatorioCadeiaFrio", f"Erro ao exportar CSV: {str(e)}")
        
        return jsonify({
            'status': 'error',
            'message': 'Erro ao exportar CSV'
        }), 500


def _get_and_validate_filters(args):
    """
    Obtém e valida filtros da requisição.
    
    Returns:
        dict: Filtros validados ou dict com 'error' se inválido
    """
    filters = {}
    
    # Intervalo de datas
    data_inicio_str = args.get('data_inicio')
    data_fim_str = args.get('data_fim')
    
    if data_inicio_str:
        try:
            filters['data_inicio'] = datetime.fromisoformat(data_inicio_str)
        except ValueError:
            return {'error': 'Data de início inválida. Use formato ISO (YYYY-MM-DD).'}
    
    if data_fim_str:
        try:
            # Fim do dia (23:59:59)
            data_fim = datetime.fromisoformat(data_fim_str)
            filters['data_fim'] = data_fim.replace(hour=23, minute=59, second=59)
        except ValueError:
            return {'error': 'Data de fim inválida. Use formato ISO (YYYY-MM-DD).'}
    
    # Validar intervalo máximo
    if 'data_inicio' in filters and 'data_fim' in filters:
        interval_days = (filters['data_fim'] - filters['data_inicio']).days
        if interval_days > MAX_INTERVAL_DAYS:
            return {
                'error': f'O intervalo máximo permitido é de {MAX_INTERVAL_DAYS} dias. '
                        f'Intervalo solicitado: {interval_days} dias.'
            }
    
    # Intervalo padrão (últimos 7 dias) se não fornecido
    if 'data_inicio' not in filters and 'data_fim' not in filters:
        filters['data_fim'] = datetime.utcnow()
        filters['data_inicio'] = filters['data_fim'] - timedelta(days=7)
    
    # Farmácia
    farmacia_id = args.get('farmacia_id')
    if farmacia_id:
        try:
            filters['farmacia_id'] = int(farmacia_id)
        except ValueError:
            return {'error': 'ID de farmácia inválido.'}
    
    # Dispositivo
    dispositivo_id = args.get('dispositivo_id')
    if dispositivo_id:
        filters['dispositivo_id'] = dispositivo_id.strip()
    
    return filters


def _build_query(filters):
    """
    Constrói query base com filtros aplicados.
    
    Args:
        filters: dict com filtros validados
        
    Returns:
        SQLAlchemy Query
    """
    query = LeituraIoT.query
    
    # Filtro de intervalo de datas
    if 'data_inicio' in filters:
        query = query.filter(LeituraIoT.data_hora >= filters['data_inicio'])
    
    if 'data_fim' in filters:
        query = query.filter(LeituraIoT.data_hora <= filters['data_fim'])
    
    # Filtro de farmácia
    if 'farmacia_id' in filters:
        query = query.filter(LeituraIoT.farmacia_id == filters['farmacia_id'])
    
    # Filtro de dispositivo
    if 'dispositivo_id' in filters:
        query = query.filter(LeituraIoT.dispositivo_id == filters['dispositivo_id'])
    
    return query


def _calculate_indicators(filters):
    """
    Calcula indicadores agregados para o conjunto filtrado.
    
    Args:
        filters: dict com filtros validados
        
    Returns:
        dict: Indicadores calculados
    """
    query = _build_query(filters)
    
    # Total de leituras
    total = query.count()
    
    if total == 0:
        return {
            'total_leituras': 0,
            'alertas_criticos': 0,
            'temperatura_min': None,
            'temperatura_max': None,
            'temperatura_media': None,
            'ultima_leitura': None
        }
    
    # Alertas críticos
    alertas_criticos = query.filter(
        LeituraIoT.status_alerta == StatusAlertaEnum.CRITICO_TERMICO
    ).count()
    
    # Temperaturas
    temp_stats = query.with_entities(
        func.min(LeituraIoT.temperatura).label('min'),
        func.max(LeituraIoT.temperatura).label('max'),
        func.avg(LeituraIoT.temperatura).label('avg')
    ).first()
    
    # Última leitura
    ultima_leitura = query.order_by(
        LeituraIoT.data_hora.desc()
    ).first()
    
    return {
        'total_leituras': total,
        'alertas_criticos': alertas_criticos,
        'temperatura_min': round(temp_stats.min, 2) if temp_stats.min else None,
        'temperatura_max': round(temp_stats.max, 2) if temp_stats.max else None,
        'temperatura_media': round(temp_stats.avg, 2) if temp_stats.avg else None,
        'ultima_leitura': ultima_leitura.data_hora.isoformat() if ultima_leitura else None
    }


def _get_paginated_readings(filters, page, per_page):
    """
    Obtém leituras paginadas.
    
    Args:
        filters: dict com filtros validados
        page: número da página (1-based)
        per_page: itens por página
        
    Returns:
        list: leituras formatadas
    """
    query = _build_query(filters)
    
    # Ordenar por data/hora descendente (mais recente primeiro)
    query = query.order_by(LeituraIoT.data_hora.desc())
    
    # Paginar
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Formatar resultados
    readings = []
    for reading in paginated.items:
        readings.append({
            'id': reading.id,
            'data_hora': reading.data_hora.isoformat() if reading.data_hora else None,
            'dispositivo_id': reading.dispositivo_id,
            'farmacia_id': reading.farmacia_id,
            'temperatura': reading.temperatura,
            'umidade': reading.umidade,
            'luminosidade_lux': reading.luminosidade_lux,
            'status_alerta': reading.status_alerta.value
        })
    
    return readings


def _get_readings_for_export(filters):
    """
    Obtém leituras para exportação (sem paginação, com limite).
    
    Args:
        filters: dict com filtros validados
        
    Returns:
        list: objetos LeituraIoT
    """
    query = _build_query(filters)
    
    # Ordenar por data/hora ascendente (cronológico)
    query = query.order_by(LeituraIoT.data_hora.asc())
    
    # Limitar
    query = query.limit(MAX_EXPORT_ROWS + 1)  # +1 para verificar se excede
    
    return query.all()


def _sanitize_csv_field(value):
    """
    Sanitiza campo para prevenir CSV injection.
    
    Se o valor começar com =, +, -, @, adiciona um prefixo.
    
    Args:
        value: valor a sanitizar
        
    Returns:
        str: valor sanitizado
    """
    if value is None:
        return ''
    
    str_value = str(value)
    
    # Prevenir fórmulas CSV
    if str_value.startswith(('=', '+', '-', '@')):
        return "'" + str_value
    
    return str_value
