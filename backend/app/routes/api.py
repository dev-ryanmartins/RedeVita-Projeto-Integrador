from datetime import datetime, timedelta
import time
import psutil
import os
from io import BytesIO

from flask import Blueprint, request, current_app
from sqlalchemy import or_, func

from app.core.api_responses import resposta_ok, resposta_erro
from app.core.decorators import admin_required, cargo_required, farmaceutico_required
from app.core.jwt_auth import jwt_ou_sessao_required
from app.database import db
from app.models.doacao import Doacao
from app.models.farmacia import Farmacia
from app.models.medicamento import Medicamento
from app.models.medico import Medico
from app.models.iot import LeituraIoT, TagRFID, StatusAlertaEnum
from app.models.usuario import Usuario
from app.schemas.med_schema import validar_entrada_medicamento
from app.utils.log_helper import registrar_log
from app.utils.semaforo import calcular_status_semaforo
from app.utils.system_health import get_health_summary
from app.utils.iot_telemetry import processar_leitura_iot, iot_simulator, autenticar_rfid
from app.utils.pdf_generator import obter_gerador_pdf
from app.extensions import limiter

api_bp = Blueprint("api", __name__, url_prefix="/api")

TARJAS_VALIDAS = ["Sem Tarja", "Tarja Amarela", "Tarja Vermelha", "Portaria 344"]


def _get_pagination_params():
    """Extract pagination parameters from request."""
    try:
        page = max(1, int(request.args.get("page", 1)))
        limit = max(1, min(100, int(request.args.get("limit", 20))))
        sort_by = request.args.get("sort_by", "id")
        sort_order = request.args.get("sort_order", "desc")
        search = request.args.get("search", "").strip()
        return page, limit, sort_by, sort_order, search
    except (ValueError, TypeError):
        return 1, 20, "id", "desc", ""


def _serializar_medicamento(med):
    return {
        "id": med.id,
        "nome": med.nome,
        "lote": med.lote,
        "data_validade": med.data_validade.isoformat(),
        "data_validade_fmt": med.data_validade.strftime("%d/%m/%Y"),
        "quantidade": med.quantidade,
        "status_semaforo": med.status_semaforo,
        "tarja": med.tarja,
        "principio_ativo": med.principio_ativo,
        "uso_continuo": med.uso_continuo,
        "controlado": med.controlado,
        "tipo_receita_requerida": med.tipo_receita_requerida,
    }


def _serializar_farmacia(f):
    return {
        "id": f.id,
        "nome": f.nome_fantasia,
        "endereco": f.endereco,
        "cnpj": f.cnpj,
        "responsavel": f.responsavel,
    }


@api_bp.route("/inventario")
@jwt_ou_sessao_required
@limiter.limit("30 per minute")
def listar_inventario():
    page, limit, sort_by, sort_order, search = _get_pagination_params()

    query = Medicamento.query

    if search:
        query = query.filter(
            or_(
                Medicamento.nome.ilike(f"%{search}%"),
                Medicamento.principio_ativo.ilike(f"%{search}%"),
                Medicamento.lote.ilike(f"%{search}%"),
            )
        )

    sort_column = getattr(Medicamento, sort_by, Medicamento.id)
    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    paginated = query.paginate(page=page, per_page=limit, error_out=False)

    medicamentos = paginated.items
    total_controlados = sum(1 for m in medicamentos if m.controlado)
    total_continuo = sum(1 for m in medicamentos if m.uso_continuo)

    return resposta_ok(
        {
            "medicamentos": [_serializar_medicamento(m) for m in medicamentos],
            "total": paginated.total,
            "pages": paginated.pages,
            "current_page": page,
            "per_page": limit,
            "total_controlados": total_controlados,
            "total_continuo": total_continuo,
            "has_next": paginated.has_next,
            "has_prev": paginated.has_prev,
        }
    )


@api_bp.route("/inventario", methods=["POST"])
@jwt_ou_sessao_required
@farmaceutico_required
def criar_medicamento_api():
    dados = request.get_json(silent=True) or {}
    campos = {
        "nome": str(dados.get("nome", "")).strip(),
        "lote": str(dados.get("lote", "")).strip(),
        "data_validade": str(dados.get("data_validade", "")).strip(),
        "quantidade": str(dados.get("quantidade", "")).strip(),
    }

    valido, erros = validar_entrada_medicamento(campos)
    if not valido:
        return resposta_erro("Dados inválidos.", 422, detalhes=erros)

    tarja = str(dados.get("tarja", "Sem Tarja")).strip()
    if tarja not in TARJAS_VALIDAS:
        tarja = "Sem Tarja"

    try:
        data_dt = datetime.strptime(campos["data_validade"], "%Y-%m-%d").date()
        med = Medicamento(
            nome=campos["nome"],
            lote=campos["lote"],
            data_validade=data_dt,
            quantidade=int(campos["quantidade"]),
            status_semaforo=calcular_status_semaforo(data_dt),
            tarja=tarja,
            principio_ativo=dados.get("principio_ativo") or None,
            uso_continuo=bool(dados.get("uso_continuo")),
            referencia_id=dados.get("referencia_id"),
        )
        db.session.add(med)
        db.session.commit()
        registrar_log("Novo Medicamento", f'"{med.nome}" cadastrado via API')
        return resposta_ok(_serializar_medicamento(med), "Medicamento cadastrado.", 201)
    except Exception:
        db.session.rollback()
        return resposta_erro("Erro ao cadastrar medicamento.", 500)


@api_bp.route("/inventario/<int:med_id>", methods=["DELETE"])
@jwt_ou_sessao_required
@admin_required
def excluir_medicamento_api(med_id):
    med = db.session.get(Medicamento, med_id)
    if not med:
        return resposta_erro("Medicamento não encontrado.", 404)
    try:
        nome = med.nome
        db.session.delete(med)
        db.session.commit()
        registrar_log("Exclusão de Medicamento", f'"{nome}" removido via API')
        return resposta_ok(mensagem=f'Medicamento "{nome}" removido.')
    except Exception:
        db.session.rollback()
        return resposta_erro("Erro ao remover medicamento.", 500)


@api_bp.route("/triagem/recentes")
@jwt_ou_sessao_required
@cargo_required("Admin", "Operador", "Farmacêutico")
def triagem_recentes():
    recentes = Medicamento.query.order_by(Medicamento.id.desc()).limit(20).all()
    return resposta_ok([_serializar_medicamento(m) for m in recentes])


@api_bp.route("/triagem", methods=["POST"])
@jwt_ou_sessao_required
@cargo_required("Admin", "Operador", "Farmacêutico")
def triagem_entrada():
    dados = request.get_json(silent=True) or {}
    nome = str(dados.get("nome", "")).strip()
    lote = str(dados.get("lote", "")).strip()
    data_validade_str = str(dados.get("data_validade", "")).strip()
    quantidade_str = str(dados.get("quantidade", "")).strip()
    tarja = str(dados.get("tarja", "Sem Tarja")).strip()
    doador = str(dados.get("doador", "")).strip() or "Não informado"
    observacoes = dados.get("observacoes")

    if not nome or not lote or not data_validade_str or not quantidade_str:
        return resposta_erro("Preencha todos os campos obrigatórios.", 422)

    try:
        quantidade = int(quantidade_str)
        if quantidade <= 0:
            raise ValueError
    except ValueError:
        return resposta_erro("Quantidade inválida.", 422)

    try:
        data_validade = datetime.strptime(data_validade_str, "%Y-%m-%d").date()
    except ValueError:
        return resposta_erro("Data de validade inválida.", 422)

    if tarja not in TARJAS_VALIDAS:
        tarja = "Sem Tarja"

    try:
        status = calcular_status_semaforo(data_validade)
        med = Medicamento(
            nome=nome,
            lote=lote,
            data_validade=data_validade,
            quantidade=quantidade,
            status_semaforo=status,
            tarja=tarja,
            principio_ativo=dados.get("principio_ativo") or None,
        )
        db.session.add(med)
        db.session.commit()
        registrar_log(
            "Triagem — Entrada de Medicamento",
            f'"{nome}" recebido de "{doador}" via API'
            + (f" | Obs: {observacoes}" if observacoes else ""),
        )

        aviso = "Medicamento adicionado ao estoque."
        if status == 2:
            aviso = f'"{nome}" adicionado, mas o lote está vencido.'
        elif status == 1:
            aviso = f'"{nome}" adicionado. Lote próximo ao vencimento.'

        return resposta_ok(_serializar_medicamento(med), aviso, 201)
    except Exception:
        db.session.rollback()
        return resposta_erro("Erro ao registrar medicamento.", 500)


@api_bp.route("/farmacias")
@jwt_ou_sessao_required
@limiter.limit("30 per minute")
def listar_farmacias():
    page, limit, sort_by, sort_order, search = _get_pagination_params()

    query = Farmacia.query

    if search:
        query = query.filter(
            or_(
                Farmacia.nome_fantasia.ilike(f"%{search}%"),
                Farmacia.razao_social.ilike(f"%{search}%"),
                Farmacia.endereco.ilike(f"%{search}%"),
            )
        )

    sort_column = getattr(Farmacia, sort_by, Farmacia.nome_fantasia)
    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    paginated = query.paginate(page=page, per_page=limit, error_out=False)

    return resposta_ok(
        {
            "farmacias": [_serializar_farmacia(f) for f in paginated.items],
            "total": paginated.total,
            "pages": paginated.pages,
            "current_page": page,
            "per_page": limit,
            "has_next": paginated.has_next,
            "has_prev": paginated.has_prev,
        }
    )


@api_bp.route("/doacoes/recentes")
@jwt_ou_sessao_required
@limiter.limit("30 per minute")
def doacoes_recentes():
    page, limit, sort_by, sort_order, search = _get_pagination_params()

    query = Doacao.query

    if search:
        query = query.join(Medicamento).filter(
            or_(
                Medicamento.nome.ilike(f"%{search}%"),
                Medicamento.lote.ilike(f"%{search}%"),
            )
        )

    sort_column = getattr(Doacao, sort_by, Doacao.data_doacao)
    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    paginated = query.paginate(page=page, per_page=limit, error_out=False)

    lista = []
    for d in paginated.items:
        lista.append(
            {
                "id": d.id,
                "medicamento": d.medicamento.nome if d.medicamento else "—",
                "quantidade": d.quantidade,
                "data": (
                    d.data_doacao.strftime("%d/%m/%Y %H:%M") if d.data_doacao else "—"
                ),
                "usuario": d.usuario.nome if d.usuario else "—",
            }
        )

    return resposta_ok(
        {
            "doacoes": lista,
            "total": paginated.total,
            "pages": paginated.pages,
            "current_page": page,
            "per_page": limit,
            "has_next": paginated.has_next,
            "has_prev": paginated.has_prev,
        }
    )


@api_bp.route("/dashboard/stats")
@jwt_ou_sessao_required
@limiter.limit("20 per minute")
def dashboard_stats():
    from sqlalchemy import func
    from datetime import date, timedelta

    hoje = date.today()
    seis_meses_atras = hoje - timedelta(days=180)

    try:
        total_medicamentos = Medicamento.query.count()
    except Exception:
        total_medicamentos = 0

    try:
        total_farmacias = Farmacia.query.count()
    except Exception:
        total_farmacias = 0

    try:
        total_doacoes = Doacao.query.count()
    except Exception:
        total_doacoes = 0

    try:
        proximos_vencimento = Medicamento.query.filter(
            Medicamento.status_semaforo == 1
        ).count()
    except Exception:
        proximos_vencimento = 0

    try:
        vencidos = Medicamento.query.filter(Medicamento.status_semaforo == 2).count()
    except Exception:
        vencidos = 0

    doacoes_6_meses = (
        db.session.query(
            func.date(Doacao.data_doacao).label("data"),
            func.count(Doacao.id).label("total"),
        )
        .filter(Doacao.data_doacao >= seis_meses_atras)
        .group_by(func.date(Doacao.data_doacao))
        .order_by(func.date(Doacao.data_doacao))
        .all()
    )

    doacoes_chart = [{"data": str(d.data), "total": d.total} for d in doacoes_6_meses]

    tarja_stats = (
        db.session.query(Medicamento.tarja, func.count(Medicamento.id))
        .group_by(Medicamento.tarja)
        .all()
    )

    tarja_chart = [{"tarja": t[0], "total": t[1]} for t in tarja_stats]

    return resposta_ok(
        {
            "total_medicamentos": total_medicamentos,
            "total_farmacias": total_farmacias,
            "total_doacoes": total_doacoes,
            "proximos_vencimento": proximos_vencimento,
            "vencidos": vencidos,
            "doacoes_chart": doacoes_chart,
            "tarja_chart": tarja_chart,
        }
    )


@api_bp.route("/v1/system-health")
@limiter.limit('60 per minute')
def system_health():
    """
    Endpoint de saúde do sistema.
    Retorna métricas de uptime, memória, CPU e status do banco de dados.
    """
    try:
        health_summary = get_health_summary(db)
        return resposta_ok(health_summary)
    except Exception as e:
        return resposta_erro(f"Erro ao obter saúde do sistema: {str(e)}", 500)


@api_bp.route("/v1/health")
@limiter.limit('60 per minute')
def health_check():
    """
    Healthcheck completo para DevOps.
    Executa teste direto de conexão ao banco (SELECT 1),
    mede uso de memória e retorna status operacional.
    """
    try:
        # Teste direto de conexão ao banco
        db_status = "OK"
        db_response_time_ms = 0
        start_db = time.time()
        try:
            db.session.execute(db.text("SELECT 1"))
            db_response_time_ms = (time.time() - start_db) * 1000
        except Exception as e:
            db_status = "ERROR"
            db_response_time_ms = 0
        
        # Métricas de memória
        memory_info = psutil.virtual_memory()
        memory_percent = memory_info.percent
        memory_used_mb = memory_info.used / (1024 * 1024)
        memory_total_mb = memory_info.total / (1024 * 1024)
        
        # Métricas de CPU
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # Uptime do processo
        uptime_seconds = time.time() - psutil.Process(os.getpid()).create_time()
        
        # Status geral
        overall_status = "OK" if db_status == "OK" else "ERROR"
        
        return resposta_ok({
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "database": {
                "status": db_status,
                "response_time_ms": round(db_response_time_ms, 2)
            },
            "system": {
                "cpu_percent": round(cpu_percent, 2),
                "memory_percent": round(memory_percent, 2),
                "memory_used_mb": round(memory_used_mb, 2),
                "memory_total_mb": round(memory_total_mb, 2),
                "uptime_seconds": round(uptime_seconds, 2)
            }
        })
    except Exception as e:
        return resposta_erro(f"Healthcheck failed: {str(e)}", 500)


@api_bp.route("/v1/analytics/stats")
@jwt_ou_sessao_required
@limiter.limit('30 per minute')
def analytics_stats():
    """
    Endpoint de estatísticas agregadas para analytics.
    Calcula estoque crítico, doações do mês e total de atendimentos.
    """
    try:
        from datetime import date, timedelta
        from app.models.paciente import Paciente
        
        hoje = date.today()
        primeiro_dia_mes = hoje.replace(day=1)
        
        # Estoque crítico (quantidade < 10 ou vencendo em 30 dias)
        trinta_dias_frente = hoje + timedelta(days=30)
        try:
            estoque_critico = Medicamento.query.filter(
                (Medicamento.quantidade < 10) |
                (Medicamento.data_validade <= trinta_dias_frente)
            ).count()
        except Exception:
            estoque_critico = 0
        
        # Doações do mês atual
        try:
            doacoes_mes = Doacao.query.filter(
                Doacao.data_doacao >= primeiro_dia_mes
            ).count()
        except Exception:
            doacoes_mes = 0
        
        # Total de atendimentos (pacientes cadastrados)
        try:
            total_atendimentos = Paciente.query.count()
        except Exception:
            total_atendimentos = 0
        
        # Percentual de estoque crítico
        try:
            total_medicamentos = Medicamento.query.count()
        except Exception:
            total_medicamentos = 0
        percentual_critico = (
            (estoque_critico / total_medicamentos * 100)
            if total_medicamentos > 0 else 0
        )
        
        # Medicamentos vencidos
        try:
            vencidos = Medicamento.query.filter(
                Medicamento.status_semaforo == 2
            ).count()
        except Exception:
            vencidos = 0
        
        # Medicamentos próximos ao vencimento
        try:
            proximos_vencimento = Medicamento.query.filter(
                Medicamento.status_semaforo == 1
            ).count()
        except Exception:
            proximos_vencimento = 0
        
        return resposta_ok({
            "estoque": {
                "total_medicamentos": total_medicamentos,
                "estoque_critico": estoque_critico,
                "percentual_critico": round(percentual_critico, 2),
                "vencidos": vencidos,
                "proximos_vencimento": proximos_vencimento,
                "status_estoque": "crítico" if percentual_critico > 20 else "normal"
            },
            "doacoes": {
                "doacoes_mes": doacoes_mes,
                "total_doacoes": Doacao.query.count() or 0
            },
            "atendimentos": {
                "total_pacientes": total_atendimentos,
                "total_medicos": Medico.query.count() or 0,
                "total_farmacias": Farmacia.query.count() or 0
            },
            "periodo": {
                "data_atual": hoje.isoformat(),
                "primeiro_dia_mes": primeiro_dia_mes.isoformat()
            }
        })
    except Exception as e:
        return resposta_erro(f"Erro ao obter estatísticas: {str(e)}", 500)


@api_bp.route("/metrics/performance")
@jwt_ou_sessao_required
@limiter.limit('60 per minute')
def performance_metrics():
    """
    Endpoint de métricas de performance da aplicação em tempo real.
    Retorna estatísticas agregadas e indicadores de saúde do sistema.
    """
    start_time = time.time()
    
    try:
        # Métricas de negócio
        try:
            total_medicamentos = Medicamento.query.count()
        except Exception:
            total_medicamentos = 0
        
        try:
            total_doacoes = Doacao.query.count()
        except Exception:
            total_doacoes = 0
        
        # Doações ativas (últimos 30 dias)
        trinta_dias_atras = datetime.utcnow() - timedelta(days=30)
        try:
            doacoes_ativas = Doacao.query.filter(Doacao.data_doacao >= trinta_dias_atras).count()
        except Exception:
            doacoes_ativas = 0
        
        # Estoque crítico (quantidade < 10 ou vencendo em 30 dias)
        try:
            estoque_baixo = Medicamento.query.filter(
                (Medicamento.quantidade < 10) | 
                (Medicamento.status_semaforo.in_([1, 2]))
            ).count()
        except Exception:
            estoque_baixo = 0
        
        porcentagem_estoque_critico = (
            (estoque_baixo / total_medicamentos * 100) 
            if total_medicamentos > 0 else 0
        )
        
        # Métricas de sistema
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory_info = psutil.virtual_memory()
        memory_percent = memory_info.percent
        memory_used_mb = memory_info.used / (1024 * 1024)
        memory_total_mb = memory_info.total / (1024 * 1024)
        
        # Tempo de resposta
        response_time = (time.time() - start_time) * 1000  # em milissegundos
        
        # Status do banco de dados
        db_status = "healthy"
        try:
            db.session.execute(db.text("SELECT 1"))
        except Exception:
            db_status = "unhealthy"
        
        # Uptime do processo (em segundos)
        uptime = time.time() - psutil.Process(os.getpid()).create_time()
        
        return resposta_ok({
            "business_metrics": {
                "total_medicamentos": total_medicamentos,
                "total_doacoes": total_doacoes,
                "doacoes_ativas_30d": doacoes_ativas,
                "estoque_critico": estoque_baixo,
                "porcentagem_estoque_critico": round(porcentagem_estoque_critico, 2),
                "status_estoque": "crítico" if porcentagem_estoque_critico > 20 else "normal"
            },
            "system_metrics": {
                "cpu_percent": round(cpu_percent, 2),
                "memory_percent": round(memory_percent, 2),
                "memory_used_mb": round(memory_used_mb, 2),
                "memory_total_mb": round(memory_total_mb, 2),
                "uptime_seconds": round(uptime, 2),
                "uptime_formatted": f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m"
            },
            "performance_metrics": {
                "response_time_ms": round(response_time, 2),
                "db_status": db_status,
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        return resposta_erro(f"Erro ao obter métricas: {str(e)}", 500)


@api_bp.route("/analytics/stock-prediction")
@jwt_ou_sessao_required
@limiter.limit('30 per minute')
def stock_prediction():
    """
    Endpoint de predição de estoque futuro.
    Analisa histórico de entradas e saídas para prever esgotamento de lotes.
    """
    try:
        from app.utils.predictive_stock import get_stock_prediction, get_stock_summary
        
        # Parâmetro opcional para medicamento específico
        medicamento_id = request.args.get('medicamento_id', type=int)
        
        if medicamento_id:
            # Retorna predição para um medicamento específico
            prediction = get_stock_prediction(medicamento_id)
            if not prediction:
                return resposta_erro("Medicamento não encontrado", 404)
            return resposta_ok(prediction)
        else:
            # Retorna resumo geral e todas as predições
            summary = get_stock_summary()
            all_predictions = get_stock_prediction()
            
            return resposta_ok({
                "resumo": summary,
                "predicoes": all_predictions
            })
            
    except Exception as e:
        return resposta_erro(f"Erro ao obter predição de estoque: {str(e)}", 500)


@api_bp.route("/iot/telemetria", methods=["POST"])
@limiter.limit('60 per minute')
def receber_telemetria_iot():
    """
    Endpoint para receber dados de telemetria IoT de sensores térmicos.
    Conforme normas ANVISA RDC 44/2009 e RDC 430/2020 para cadeia de frio.
    
    Regras sanitárias aplicadas:
    - Normal: 15.0°C <= Temp <= 25.0°C e Umidade <= 70% -> Status: NORMAL
    - Alerta: (10.0°C <= Temp < 15.0°C) ou (25.0°C < Temp <= 30.0°C) -> Status: ALERTA_LEVE
    - Crítico: Temp > 30.0°C ou Temp < 10.0°C -> Status: CRITICO_TERMICO
    
    Expected JSON payload:
    {
        "dispositivo_id": str (required),
        "temperatura": float (required),
        "umidade": float (required),
        "farmacia_id": int (optional),
        "timestamp": str (ISO-8601, optional)
    }
    """
    try:
        dados = request.get_json()
        
        if not dados:
            return resposta_erro("Dados não fornecidos", 400)
        
        dispositivo_id = dados.get('dispositivo_id')
        temperatura = dados.get('temperatura')
        umidade = dados.get('umidade')
        luminosidade_lux = dados.get('luminosidade_lux')
        farmacia_id = dados.get('farmacia_id')
        timestamp_str = dados.get('timestamp')
        
        # Validação de campos obrigatórios
        if not dispositivo_id:
            return resposta_erro("dispositivo_id é obrigatório", 400)
        if temperatura is None:
            return resposta_erro("temperatura é obrigatória", 400)
        if umidade is None:
            return resposta_erro("umidade é obrigatória", 400)
        
        # Validação de tipos
        try:
            temperatura = float(temperatura)
            umidade = float(umidade)
            if luminosidade_lux is not None:
                luminosidade_lux = float(luminosidade_lux)
        except (ValueError, TypeError):
            return resposta_erro("temperatura, umidade e luminosidade devem ser números", 400)
        
        # Validação de faixas
        if temperatura < -50 or temperatura > 100:
            return resposta_erro("temperatura fora de faixa válida (-50°C a 100°C)", 400)
        if umidade < 0 or umidade > 100:
            return resposta_erro("umidade fora de faixa válida (0% a 100%)", 400)
        if luminosidade_lux is not None and (luminosidade_lux < 0 or luminosidade_lux > 100000):
            return resposta_erro("luminosidade fora de faixa válida (0 a 100000 lux)", 400)
        
        # Aplica regras sanitárias ANVISA
        if temperatura >= 15.0 and temperatura <= 25.0 and umidade <= 70:
            status_alerta = StatusAlertaEnum.NORMAL
        elif (
            (temperatura >= 10.0 and temperatura < 15.0)
            or (temperatura > 25.0 and temperatura <= 30.0)
            or (temperatura >= 15.0 and temperatura <= 25.0 and umidade > 70.0)
        ):
            status_alerta = StatusAlertaEnum.ALERTA_LEVE
        else:
            status_alerta = StatusAlertaEnum.CRITICO_TERMICO
        
        # Processa timestamp se fornecido
        data_hora = datetime.utcnow()
        if timestamp_str:
            try:
                from dateutil.parser import isoparse
                data_hora = isoparse(timestamp_str)
            except Exception:
                return resposta_erro("timestamp em formato inválido (use ISO-8601)", 400)
        
        # Cria registro no banco de dados
        leitura = LeituraIoT(
            dispositivo_id=dispositivo_id,
            farmacia_id=farmacia_id,
            temperatura=temperatura,
            umidade=umidade,
            luminosidade_lux=luminosidade_lux,
            status_alerta=status_alerta,
            data_hora=data_hora
        )
        
        db.session.add(leitura)
        db.session.commit()
        
        # Verificação de fotodegradação (luminosidade > 500 lux)
        if luminosidade_lux and luminosidade_lux > 500.0:
            # Verifica se há medicamentos fotossensíveis na farmácia
            if farmacia_id:
                from app.models.medicamento import Medicamento
                medicamentos_fotossensiveis = Medicamento.query.filter(
                    Medicamento.farmacia_id == farmacia_id,
                    Medicamento.fotossensivel == True
                ).count()
                
                if medicamentos_fotossensiveis > 0:
                    registrar_log(
                        "ALERTA_FOTOSSENSIBILIDADE",
                        f"ALERTA DE FOTODEGRADAÇÃO - Dispositivo {dispositivo_id}: "
                        f"Luminosidade {luminosidade_lux} lux (>500 lux) detectada. "
                        f"{medicamentos_fotossensiveis} medicamento(s) fotossensível(is) em risco."
                    )
        
        # Ações em caso de CRITICO_TERMICO
        if status_alerta == StatusAlertaEnum.CRITICO_TERMICO:
            # Registra alerta na tabela logs_atividade
            registrar_log(
                "VIOLAÇÃO_TERMICIDADE_IOT",
                f"VIOLAÇÃO CRÍTICA DE CADEIA DE FRIO - Dispositivo {dispositivo_id}: "
                f"Temperatura {temperatura}°C, Umidade {umidade}% - "
                f"Fora dos limites ANVISA (10°C - 30°C)"
            )
            
            # Dispara notificação interna para Farmacêutico e Admin
            from app.utils.notificacoes import enviar_alerta_estoque
            try:
                enviar_alerta_estoque(
                    f"ALERTA CRÍTICO IoT - Dispositivo {dispositivo_id}",
                    f"Temperatura {temperatura}°C fora dos limites ANVISA. Ação imediata necessária!"
                )
            except Exception as e:
                current_app.logger.error(f"Erro ao enviar notificação IoT: {str(e)}")
        
        return resposta_ok({
            'id': leitura.id,
            'dispositivo_id': leitura.dispositivo_id,
            'temperatura': leitura.temperatura,
            'umidade': leitura.umidade,
            'status_alerta': leitura.status_alerta.value,
            'data_hora': leitura.data_hora.isoformat(),
            'alerta_critico': status_alerta == StatusAlertaEnum.CRITICO_TERMICO
        }, "Telemetria recebida com sucesso", 201)
        
    except Exception as e:
        db.session.rollback()
        return resposta_erro(f"Erro ao processar telemetria: {str(e)}", 500)


@api_bp.route("/iot/telemetria/atual")
@jwt_ou_sessao_required
@limiter.limit('30 per minute')
def obter_status_iot_atual():
    """
    Endpoint para consultar o status atual da rede de frio IoT.
    Retorna última leitura, média das últimas 24h e status geral.
    """
    try:
        # Obtém última leitura
        ultima_leitura = LeituraIoT.query.order_by(LeituraIoT.data_hora.desc()).first()
        
        # Calcula média das últimas 24 horas
        desde_24h = datetime.utcnow() - timedelta(hours=24)
        leituras_24h = LeituraIoT.query.filter(LeituraIoT.data_hora >= desde_24h).all()
        
        if leituras_24h:
            media_temp = sum(l.temperatura for l in leituras_24h) / len(leituras_24h)
            media_umid = sum(l.umidade for l in leituras_24h) / len(leituras_24h)
        else:
            media_temp = None
            media_umid = None
        
        # Conta alertas críticos nas últimas 24h
        try:
            criticos_24h = LeituraIoT.query.filter(
                LeituraIoT.data_hora >= desde_24h,
                LeituraIoT.status_alerta == StatusAlertaEnum.CRITICO_TERMICO
            ).count()
        except Exception:
            criticos_24h = 0
        
        # Status geral da rede
        if ultima_leitura:
            status_geral = ultima_leitura.status_alerta.value
        else:
            status_geral = 'sem_dados'
        
        try:
            total_dispositivos = db.session.query(LeituraIoT.dispositivo_id).distinct().count()
        except Exception:
            total_dispositivos = 0
        
        return resposta_ok({
            'ultima_leitura': ultima_leitura.to_dict() if ultima_leitura else None,
            'media_24h': {
                'temperatura': round(media_temp, 2) if media_temp is not None else None,
                'umidade': round(media_umid, 2) if media_umid is not None else None,
                'total_leituras': len(leituras_24h)
            },
            'alertas_criticos_24h': criticos_24h,
            'status_geral': status_geral,
            'total_dispositivos': total_dispositivos
        })
        
    except Exception as e:
        return resposta_erro(f"Erro ao obter status IoT: {str(e)}", 500)


@api_bp.route("/iot/telemetria/sensores")
@jwt_ou_sessao_required
@limiter.limit('30 per minute')
def listar_sensores_iot():
    """
    Endpoint para listar todos os sensores configurados e suas leituras atuais.
    """
    try:
        leituras = iot_simulator.obter_todas_leituras()
        return resposta_ok({
            "sensores": leituras,
            "total": len(leituras)
        })
    except Exception as e:
        return resposta_erro(f"Erro ao listar sensores: {str(e)}", 500)


@api_bp.route("/iot/telemetria/<sensor_key>")
@jwt_ou_sessao_required
@limiter.limit('30 per minute')
def obter_leitura_sensor(sensor_key):
    """
    Endpoint para obter a leitura atual de um sensor específico.
    """
    try:
        leitura = iot_simulator.obter_leitura_atual(sensor_key)
        
        if not leitura:
            return resposta_erro("Sensor não encontrado", 404)
        
        return resposta_ok(leitura)
    except Exception as e:
        return resposta_erro(f"Erro ao obter leitura: {str(e)}", 500)


@api_bp.route("/relatorios/pdf", methods=["POST"])
@jwt_ou_sessao_required
@limiter.limit('10 per minute')
def gerar_pdf_relatorio():
    """
    Endpoint para gerar PDF de relatórios (doação ou retirada).
    Gera PDF assíncrono e retorna o arquivo para download.
    """
    try:
        dados = request.get_json()
        
        if not dados:
            return resposta_erro("Dados não fornecidos", 400)
        
        tipo = dados.get('tipo')  # 'doacao' ou 'retirada'
        
        if tipo not in ['doacao', 'retirada']:
            return resposta_erro("Tipo deve ser 'doacao' ou 'retirada'", 400)
        
        gerador = obter_gerador_pdf()
        
        if tipo == 'doacao':
            pdf_bytes = gerador.gerar_pdf_doacao(dados)
            nome_arquivo = f"comprovante_doacao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        else:
            pdf_bytes = gerador.gerar_pdf_retirada(dados)
            nome_arquivo = f"ordem_retirada_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        from flask import send_file
        
        return send_file(
            BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=nome_arquivo
        )
        
    except ImportError:
        return resposta_erro("Biblioteca reportlab não instalada. Instale com: pip install reportlab", 500)
    except Exception as e:
        return resposta_erro(f"Erro ao gerar PDF: {str(e)}", 500)


@api_bp.route("/iot/rfid-autenticar", methods=["POST"])
@limiter.limit('30 per minute')
def autenticar_rfid_iot():
    """
    Endpoint para autenticação RFID/NFC do farmacêutico.
    Valida a tag no banco de dados e registra abertura da gaveta de estoque.
    
    Expected JSON payload:
    {
        "tag_uid": str (required),
        "armario_id": str (optional, default: 'CONTROLADOS')
    }
    """
    try:
        dados = request.get_json()
        
        if not dados:
            return resposta_erro("Dados não fornecidos", 400)
        
        tag_uid = dados.get('tag_uid')
        armario_id = dados.get('armario_id', 'CONTROLADOS')
        
        if not tag_uid:
            return resposta_erro("tag_uid é obrigatório", 400)
        
        # Busca a tag no banco de dados
        tag_rfid = TagRFID.query.filter_by(tag_uid=tag_uid).first()
        
        if not tag_rfid:
            # Tag não encontrada - possível violação
            registrar_log(
                "SEGURANÇA - Tentativa de Violação de Armário Físico",
                f"Tag RFID não cadastrada tentou acessar armário {armario_id}: {tag_uid}"
            )
            return resposta_erro(
                {"autorizado": False, "mensagem": "Acesso Negado à Trava Física - Tag não reconhecida"},
                403
            )
        
        # Verifica se a tag está ativa
        if not tag_rfid.ativo:
            registrar_log(
                "SEGURANÇA - Tentativa de Acesso com Tag Desativada",
                f"Tag RFID desativada tentou acessar armário {armario_id}: Usuário ID {tag_rfid.usuario_id}"
            )
            return resposta_erro(
                {"autorizado": False, "mensagem": "Acesso Negado à Trava Física - Tag desativada"},
                403
            )
        
        # Busca o usuário associado
        usuario = Usuario.query.get(tag_rfid.usuario_id)
        
        if not usuario:
            return resposta_erro(
                {"autorizado": False, "mensagem": "Acesso Negado à Trava Física - Usuário não encontrado"},
                403
            )
        
        # Verifica se o usuário tem permissão (farmaceutico ou admin)
        if usuario.cargo.lower() not in ['farmacêutico', 'admin']:
            registrar_log(
                "SEGURANÇA - Tentativa de Violação de Armário Físico",
                f"Usuário sem privilégios tentou acessar armário {armario_id}: "
                f"{usuario.nome} (Cargo: {usuario.cargo}) - Tag {tag_uid}"
            )
            return resposta_erro(
                {"autorizado": False, "mensagem": "Acesso Negado à Trava Física - Privilégios insuficientes"},
                403
            )
        
        # Autenticação bem-sucedida
        # Atualiza último acesso da tag
        tag_rfid.ultimo_acesso = datetime.utcnow()
        db.session.commit()
        
        # Registra log de auditoria
        registrar_log(
            "AUDITORIA - Abertura de Armário Autorizada",
            f"Armário {armario_id} aberto por {usuario.nome} ({usuario.cargo}) via RFID"
        )
        
        return resposta_ok({
            "autorizado": True,
            "usuario": {
                "id": usuario.id,
                "nome": usuario.nome,
                "cargo": usuario.cargo
            },
            "tag": {
                "id": tag_rfid.id,
                "descricao": tag_rfid.descricao
            },
            "armario": armario_id,
            "timestamp": datetime.utcnow().isoformat()
        }, "Autenticação RFID realizada com sucesso", 200)
        
    except Exception as e:
        db.session.rollback()
        return resposta_erro(f"Erro na autenticação RFID: {str(e)}", 500)


@api_bp.route("/iot/balanca-pesar", methods=["POST"])
@jwt_ou_sessao_required
@limiter.limit('30 per minute')
def balanca_pesar_doacao():
    """
    Endpoint para pesagem automática de doações via balança IoT.
    Compara peso real com tara de referência e sinaliza discrepâncias.
    
    Expected JSON payload:
    {
        "doacao_id": int (required),
        "peso_gramas": float (required)
    }
    """
    try:
        dados = request.get_json()
        
        if not dados:
            return resposta_erro("Dados não fornecidos", 400)
        
        doacao_id = dados.get('doacao_id')
        peso_gramas = dados.get('peso_gramas')
        
        if not doacao_id:
            return resposta_erro("doacao_id é obrigatório", 400)
        if peso_gramas is None:
            return resposta_erro("peso_gramas é obrigatório", 400)
        
        # Validação de tipo
        try:
            peso_gramas = float(peso_gramas)
        except (ValueError, TypeError):
            return resposta_erro("peso_gramas deve ser um número", 400)
        
        if peso_gramas <= 0:
            return resposta_erro("peso_gramas deve ser positivo", 400)
        
        # Busca doação
        doacao = Doacao.query.get(doacao_id)
        
        if not doacao:
            return resposta_erro("Doação não encontrada", 404)
        
        # Atualiza peso da doação
        doacao.peso_gramas = peso_gramas
        
        # Verifica discrepância com tara de referência (se existir)
        # Assume tara de referência baseada na quantidade (ex: 1 unidade = 5g)
        tara_referencia = doacao.quantidade * 5.0  # 5g por unidade como exemplo
        
        if tara_referencia > 0:
            discrepancia_percentual = abs(peso_gramas - tara_referencia) / tara_referencia * 100
            
            if discrepancia_percentual > 15.0:
                # Discrepância maior que 15% - sinaliza para conferência manual
                doacao.status_conferencia = "PENDENTE_CONFERENCIA_MANUAL"
                
                registrar_log(
                    "ALERTA_PESAGEM_IOT",
                    f"DISCREPÂNCIA DE PESO DETECTADA - Doação ID {doacao_id}: "
                    f"Peso Real: {peso_gramas}g vs Tara Referência: {tara_referencia}g "
                    f"(Discrepância: {discrepancia_percentual:.1f}%). "
                    f"Marcada para conferência manual."
                )
                
                return resposta_ok({
                    'doacao_id': doacao.id,
                    'peso_gramas': peso_gramas,
                    'tara_referencia': tara_referencia,
                    'discrepancia_percentual': round(discrepancia_percentual, 2),
                    'status_conferencia': doacao.status_conferencia,
                    'mensagem': 'Discrepância detectada (>15%). Doação marcada para conferência manual.'
                }, "Pesagem registrada com alerta", 200)
            else:
                # Peso dentro da tolerância
                doacao.status_conferencia = "APROVADO"
                
                return resposta_ok({
                    'doacao_id': doacao.id,
                    'peso_gramas': peso_gramas,
                    'tara_referencia': tara_referencia,
                    'discrepancia_percentual': round(discrepancia_percentual, 2),
                    'status_conferencia': doacao.status_conferencia,
                    'mensagem': 'Pesagem aprovada (dentro da tolerância de 15%).'
                }, "Pesagem registrada com sucesso", 200)
        else:
            # Sem tara de referência - apenas registra
            return resposta_ok({
                'doacao_id': doacao.id,
                'peso_gramas': peso_gramas,
                'status_conferencia': doacao.status_conferencia,
                'mensagem': 'Pesagem registrada (sem tara de referência para comparação).'
            }, "Pesagem registrada", 200)
        
    except Exception as e:
        db.session.rollback()
        return resposta_erro(f"Erro ao processar pesagem: {str(e)}", 500)


@api_bp.route("/iot/telemetria/lote", methods=["POST"])
@limiter.limit('30 per minute')
def receber_telemetria_lote():
    """
    Endpoint para receber lote de telemetria IoT (batch dispatch).
    Utilizado por dispositivos de borda para descarregar buffer offline.
    
    Expected JSON payload:
    {
        "leituras": [
            {
                "dispositivo_id": str,
                "temperatura": float,
                "umidade": float,
                "luminosidade_lux": float (optional),
                "farmacia_id": int (optional),
                "timestamp": str (ISO-8601, optional)
            },
            ...
        ]
    }
    """
    try:
        dados = request.get_json()
        
        if not dados:
            return resposta_erro("Dados não fornecidos", 400)
        
        leituras = dados.get('leituras', [])
        
        if not leituras:
            return resposta_erro("Nenhuma leitura fornecida", 400)
        
        if len(leituras) > 100:
            return resposta_erro("Máximo de 100 leituras por lote", 400)
        
        leituras_processadas = []
        erros = []
        
        for idx, leitura_data in enumerate(leituras):
            try:
                dispositivo_id = leitura_data.get('dispositivo_id')
                temperatura = leitura_data.get('temperatura')
                umidade = leitura_data.get('umidade')
                luminosidade_lux = leitura_data.get('luminosidade_lux')
                farmacia_id = leitura_data.get('farmacia_id')
                timestamp_str = leitura_data.get('timestamp')
                
                # Validação básica
                if not dispositivo_id or temperatura is None or umidade is None:
                    erros.append(f"Índice {idx}: campos obrigatórios faltando")
                    continue
                
                # Validação de tipos
                try:
                    temperatura = float(temperatura)
                    umidade = float(umidade)
                    if luminosidade_lux is not None:
                        luminosidade_lux = float(luminosidade_lux)
                except (ValueError, TypeError):
                    erros.append(f"Índice {idx}: tipos inválidos")
                    continue
                
                # Aplica regras sanitárias ANVISA
                if temperatura >= 15.0 and temperatura <= 25.0 and umidade <= 70:
                    status_alerta = StatusAlertaEnum.NORMAL
                elif (temperatura >= 10.0 and temperatura < 15.0) or (temperatura > 25.0 and temperatura <= 30.0):
                    status_alerta = StatusAlertaEnum.ALERTA_LEVE
                else:
                    status_alerta = StatusAlertaEnum.CRITICO_TERMICO
                
                # Processa timestamp
                data_hora = datetime.utcnow()
                if timestamp_str:
                    try:
                        from dateutil.parser import isoparse
                        data_hora = isoparse(timestamp_str)
                    except Exception:
                        pass  # Usa timestamp atual
                
                # Cria registro
                leitura = LeituraIoT(
                    dispositivo_id=dispositivo_id,
                    farmacia_id=farmacia_id,
                    temperatura=temperatura,
                    umidade=umidade,
                    luminosidade_lux=luminosidade_lux,
                    status_alerta=status_alerta,
                    data_hora=data_hora
                )
                
                db.session.add(leitura)
                leituras_processadas.append({
                    'dispositivo_id': dispositivo_id,
                    'temperatura': temperatura,
                    'status': status_alerta.value
                })
                
            except Exception as e:
                erros.append(f"Índice {idx}: {str(e)}")
        
        db.session.commit()
        
        return resposta_ok({
            'processadas': len(leituras_processadas),
            'total_recebidas': len(leituras),
            'erros': erros,
            'leituras': leituras_processadas
        }, f"Lote processado: {len(leituras_processadas)}/{len(leituras)} leituras", 201)
        
    except Exception as e:
        db.session.rollback()
        return resposta_erro(f"Erro ao processar lote: {str(e)}", 500)


@api_bp.route("/iot/telemetria/historico")
@jwt_ou_sessao_required
@limiter.limit('30 per minute')
def obter_historico_iot():
    """
    Endpoint para obter histórico de telemetria IoT.
    Retorna dados para visualização em gráficos.
    
    Query params:
        horas: número de horas de histórico (padrão: 24)
        dispositivo_id: filtro por dispositivo (opcional)
    """
    try:
        horas = request.args.get('horas', 24, type=int)
        dispositivo_id = request.args.get('dispositivo_id')
        
        # Limita o range máximo
        horas = min(horas, 168)  # Máximo 7 dias
        
        desde = datetime.utcnow() - timedelta(hours=horas)
        
        # Constrói query
        query = LeituraIoT.query.filter(LeituraIoT.data_hora >= desde)
        
        if dispositivo_id:
            query = query.filter(LeituraIoT.dispositivo_id == dispositivo_id)
        
        leituras = query.order_by(LeituraIoT.data_hora.asc()).all()
        
        # Formata dados para gráfico
        dados_grafico = []
        for leitura in leituras:
            dados_grafico.append({
                'data_hora': leitura.data_hora.isoformat(),
                'temperatura': leitura.temperatura,
                'umidade': leitura.umidade,
                'luminosidade_lux': leitura.luminosidade_lux,
                'status_alerta': leitura.status_alerta.value
            })
        
        # Calcula estatísticas
        if dados_grafico:
            temps = [d['temperatura'] for d in dados_grafico]
            umids = [d['umidade'] for d in dados_grafico]
            
            estatisticas = {
                'temperatura': {
                    'min': min(temps),
                    'max': max(temps),
                    'media': sum(temps) / len(temps)
                },
                'umidade': {
                    'min': min(umids),
                    'max': max(umids),
                    'media': sum(umids) / len(umids)
                },
                'total_leituras': len(dados_grafico)
            }
        else:
            estatisticas = None
        
        return resposta_ok({
            'dados': dados_grafico,
            'estatisticas': estatisticas,
            'periodo_horas': horas,
            'dispositivo_id': dispositivo_id
        })
        
    except Exception as e:
        return resposta_erro(f"Erro ao obter histórico: {str(e)}", 500)
