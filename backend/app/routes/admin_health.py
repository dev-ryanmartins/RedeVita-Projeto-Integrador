"""
Admin Health Dashboard - Painel de Saúde Operacional

Acesso exclusivo para administradores para monitorar indicadores operacionais
do sistema, banco de dados e telemetria IoT persistida.
"""

from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from datetime import datetime, timedelta
from sqlalchemy import func, text

from app.core.decorators import admin_required
from app.database import db
from app.models.iot import LeituraIoT, StatusAlertaEnum
from app.utils.system_health import get_system_monitor, get_health_summary

admin_health_bp = Blueprint('admin_health', __name__)


@admin_health_bp.route('/admin/painel-saude')
@login_required
@admin_required
def painel_saude():
    """
    Página do Painel de Saúde Operacional (UI).
    Acessível apenas por administradores.
    """
    return render_template('admin_painel_saude.html')


@admin_health_bp.route('/api/admin/painel-saude/dados')
@login_required
@admin_required
def painel_saude_dados():
    """
    Endpoint JSON para dados do Painel de Saúde Operacional.
    Acessível apenas por administradores.
    
    Retorna métricas do sistema e telemetria IoT agregadas.
    """
    try:
        # Métricas do sistema
        health_summary = get_health_summary(db)
        
        # Métricas IoT agregadas
        iot_metrics = _get_iot_metrics()
        
        return jsonify({
            'status': 'ok',
            'timestamp': datetime.utcnow().isoformat(),
            'system': health_summary,
            'iot': iot_metrics
        }), 200
        
    except Exception as e:
        # Log sanitizado - não expõe detalhes de erro
        from app.utils.log_helper import registrar_log
        registrar_log("PainelSaude", f"Erro ao obter dados do painel: {str(e)}")
        
        return jsonify({
            'status': 'error',
            'message': 'Erro ao carregar dados do painel',
            'timestamp': datetime.utcnow().isoformat()
        }), 500


def _get_iot_metrics():
    """
    Calcula métricas agregadas de telemetria IoT persistida.
    
    Returns:
        dict: Métricas IoT agregadas (última leitura, 24h, dispositivos, críticos)
    """
    try:
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)
        
        # Data/hora da telemetria mais recente
        ultima_leitura = db.session.query(
            func.max(LeituraIoT.data_hora)
        ).scalar()
        
        # Quantidade de leituras nas últimas 24 horas
        leituras_24h = db.session.query(
            func.count(LeituraIoT.id)
        ).filter(
            LeituraIoT.data_hora >= last_24h
        ).scalar() or 0
        
        # Quantidade de dispositivos únicos que enviaram dados nas últimas 24 horas
        dispositivos_24h = db.session.query(
            func.count(func.distinct(LeituraIoT.dispositivo_id))
        ).filter(
            LeituraIoT.data_hora >= last_24h
        ).scalar() or 0
        
        # Quantidade de leituras críticas nas últimas 24 horas
        criticas_24h = db.session.query(
            func.count(LeituraIoT.id)
        ).filter(
            LeituraIoT.data_hora >= last_24h,
            LeituraIoT.status_alerta == StatusAlertaEnum.CRITICO_TERMICO
        ).scalar() or 0
        
        # Estado "sem dados" quando não houver leituras
        if ultima_leitura is None:
            return {
                'estado': 'sem_dados',
                'ultima_leitura': None,
                'idade_horas': None,
                'leituras_24h': 0,
                'dispositivos_24h': 0,
                'criticas_24h': 0
            }
        
        # Calcular idade da última leitura em horas
        idade_horas = (now - ultima_leitura).total_seconds() / 3600
        
        # Determinar estado da telemetria
        if idade_horas > 48:
            estado = 'desatualizado'
        elif idade_horas > 24:
            estado = 'atencao'
        else:
            estado = 'saudavel'
        
        return {
            'estado': estado,
            'ultima_leitura': ultima_leitura.isoformat() if ultima_leitura else None,
            'idade_horas': round(idade_horas, 2),
            'leituras_24h': leituras_24h,
            'dispositivos_24h': dispositivos_24h,
            'criticas_24h': criticas_24h
        }
        
    except Exception as e:
        # Em caso de erro no banco, retorna estado de erro sem expor detalhes
        return {
            'estado': 'erro',
            'ultima_leitura': None,
            'idade_horas': None,
            'leituras_24h': 0,
            'dispositivos_24h': 0,
            'criticas_24h': 0,
            'erro': 'Erro ao consultar telemetria'
        }
