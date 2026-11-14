import json
import math
from flask import Blueprint, render_template, current_app, request, jsonify
from flask_login import login_required
from app.models.farmacia import Farmacia
from app.core.api_responses import resposta_ok, resposta_erro
from app.core.decorators import voluntario_required

mapa_bp = Blueprint("mapa", __name__)


def validar_coordenada(latitude: float, longitude: float) -> tuple[bool, str]:
    """
    Valida se as coordenadas são válidas e dentro dos intervalos geográficos.
    
    Args:
        latitude: Latitude a validar
        longitude: Longitude a validar
    
    Returns:
        Tuple (valido, mensagem_erro)
    """
    # Verificar se são números
    if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
        return False, "Coordenadas devem ser numéricas"
    
    # Verificar NaN ou infinito
    if math.isnan(latitude) or math.isnan(longitude):
        return False, "Coordenadas não podem ser NaN"
    if math.isinf(latitude) or math.isinf(longitude):
        return False, "Coordenadas não podem ser infinitas"
    
    # Verificar intervalos geográficos
    if not (-90 <= latitude <= 90):
        return False, f"Latitude deve estar entre -90 e 90 (recebido: {latitude})"
    if not (-180 <= longitude <= 180):
        return False, f"Longitude deve estar entre -180 e 180 (recebido: {longitude})"
    
    return True, ""


def calcular_distancia_haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcula a distância entre dois pontos geográficos usando a fórmula de Haversine.
    Disciplina: Fundamentos de IoT - Geofencing de Proximidade
    
    Args:
        lat1, lon1: Coordenadas do primeiro ponto
        lat2, lon2: Coordenadas do segundo ponto
    
    Returns:
        Distância em quilômetros
    
    Raises:
        ValueError: Se as coordenadas forem inválidas
    """
    # Validar coordenadas antes de calcular
    valido, erro = validar_coordenada(lat1, lon1)
    if not valido:
        raise ValueError(f"Coordenadas inválidas ponto 1: {erro}")
    
    valido, erro = validar_coordenada(lat2, lon2)
    if not valido:
        raise ValueError(f"Coordenadas inválidas ponto 2: {erro}")
    
    R = 6371
    
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c


@mapa_bp.route("/mapa")
@login_required
@voluntario_required
def mapa_saude():
    try:
        # Paginação para evitar carregar todas as farmácias
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 100, type=int)
        
        # Limitar per_page para máximo de 500
        per_page = min(per_page, 500)
        page = max(page, 1)
        
        cache_key = f"farmacias_map_data_page_{page}_per_{per_page}"
        farmacias_json = current_app.cache.get(cache_key)

        if farmacias_json is None:
            paginated = Farmacia.query.paginate(page=page, per_page=per_page, error_out=False)
            farmacias = paginated.items
            pontos = []
            for farmacia in farmacias:
                latitude = getattr(farmacia, "latitude", None)
                longitude = getattr(farmacia, "longitude", None)
                if latitude is None or longitude is None:
                    continue
                try:
                    latitude = float(latitude)
                    longitude = float(longitude)
                except (TypeError, ValueError):
                    continue
                pontos.append({
                    "id": farmacia.id,
                    "nome": farmacia.nome_fantasia or "Farmácia sem nome",
                    "endereco": farmacia.endereco or "Endereço não informado",
                    "cnpj": farmacia.cnpj or "",
                    "responsavel": farmacia.responsavel or "",
                    "lat": latitude,
                    "lng": longitude,
                    "tipo": "Farmácia",
                })

            farmacias_json = json.dumps({
                "pontos": pontos,
                "total": paginated.total,
                "pages": paginated.pages,
                "current_page": page,
                "per_page": per_page,
                "has_next": paginated.has_next,
                "has_prev": paginated.has_prev,
            }, ensure_ascii=False)
            current_app.cache.set(cache_key, farmacias_json, timeout=300)
        
        # Não há mais dependência de Google Maps API Key
        default_lat = -23.5015
        default_lng = -47.4526
        
        return render_template("mapa.html", farmacias_json=farmacias_json,
                              default_lat=default_lat, default_lng=default_lng)
    except Exception as e:
        current_app.logger.error(f"Erro ao carregar mapa: {str(e)}")
        farmacias_json = json.dumps({
            "pontos": [],
            "total": 0,
            "pages": 0,
            "current_page": 1,
            "per_page": per_page,
            "has_next": False,
            "has_prev": False,
        }, ensure_ascii=False)
        return render_template("mapa.html", farmacias_json=farmacias_json,
                              default_lat=-23.5015, default_lng=-47.4526)


@mapa_bp.route("/api/mapa/proximidade", methods=["POST"])
@login_required
def verificar_proximidade():
    try:
        dados = request.get_json()
        
        if not dados:
            return resposta_erro("Dados não fornecidos", 400)
        
        paciente_lat = dados.get('latitude')
        paciente_lon = dados.get('longitude')
        
        if paciente_lat is None or paciente_lon is None:
            return resposta_erro("latitude e longitude são obrigatórios", 400)
        
        # Validar tipo das coordenadas
        try:
            paciente_lat = float(paciente_lat)
            paciente_lon = float(paciente_lon)
        except (TypeError, ValueError):
            return resposta_erro("latitude e longitude devem ser números válidos", 400)
        
        # Validar intervalos das coordenadas do paciente
        valido, erro = validar_coordenada(paciente_lat, paciente_lon)
        if not valido:
            return resposta_erro(f"Coordenadas inválidas: {erro}", 400)

        LIMITE_PROXIMIDADE_KM = 1.0
        MAX_RESULTADOS = 50  # Limitar número de farmácias retornadas
        
        # Carregar farmácias com limite para evitar carregar todas se houver milhares
        # Nota: para cálculo de proximidade precisamos carregar várias, mas limitamos
        farmacias = Farmacia.query.limit(1000).all()
        farmacias_proximas = []
        
        for farmacia in farmacias:
            # Omitir farmácias sem coordenadas válidas
            farmacia_lat = getattr(farmacia, 'latitude', None)
            farmacia_lon = getattr(farmacia, 'longitude', None)
            
            if farmacia_lat is None or farmacia_lon is None:
                continue
            
            # Validar tipo das coordenadas da farmácia
            try:
                farmacia_lat = float(farmacia_lat)
                farmacia_lon = float(farmacia_lon)
            except (TypeError, ValueError):
                continue
            
            # Validar intervalos das coordenadas da farmácia
            valido, _ = validar_coordenada(farmacia_lat, farmacia_lon)
            if not valido:
                continue
            
            # Calcular distância (agora valida internamente)
            try:
                distancia = calcular_distancia_haversine(
                    paciente_lat, paciente_lon,
                    farmacia_lat, farmacia_lon
                )
                
                if distancia <= LIMITE_PROXIMIDADE_KM:
                    farmacias_proximas.append({
                        'id': farmacia.id,
                        'nome': farmacia.nome_fantasia,
                        'endereco': farmacia.endereco,
                        'distancia_km': round(distancia, 3),
                        'latitude': farmacia_lat,
                        'longitude': farmacia_lon
                    })
            except ValueError as e:
                # Coordenadas inválidas no cálculo - omitir esta farmácia
                current_app.logger.warning(f"Farmácia {farmacia.id} com coordenadas inválidas: {str(e)}")
                continue

        farmacias_proximas.sort(key=lambda f: f['distancia_km'])
        
        # Limitar número de resultados
        farmacias_proximas = farmacias_proximas[:MAX_RESULTADOS]
        
        return resposta_ok({
            'farmacias_proximas': farmacias_proximas,
            'total': len(farmacias_proximas),
            'limite_km': LIMITE_PROXIMIDADE_KM,
            'max_resultados': MAX_RESULTADOS,
            'alerta': len(farmacias_proximas) > 0,
            'mensagem': f'{len(farmacias_proximas)} farmácia(s) próxima(s) encontrada(s)' if farmacias_proximas else 'Nenhuma farmácia próxima encontrada'
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao verificar proximidade: {str(e)}")
        return resposta_erro("Erro ao verificar proximidade", 500)
