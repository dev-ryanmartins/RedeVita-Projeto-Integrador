import os
import json
import math
from flask import Blueprint, render_template, current_app, request, jsonify
from flask_login import login_required
from app.models.farmacia import Farmacia
from app.core.api_responses import resposta_ok, resposta_erro

mapa_bp = Blueprint("mapa", __name__)


def calcular_distancia_haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcula a distância entre dois pontos geográficos usando a fórmula de Haversine.
    Disciplina: Fundamentos de IoT - Geofencing de Proximidade
    
    Args:
        lat1, lon1: Coordenadas do primeiro ponto
        lat2, lon2: Coordenadas do segundo ponto
    
    Returns:
        Distância em quilômetros
    """
    R = 6371  # Raio da Terra em km
    
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c


@mapa_bp.route("/mapa")
@login_required
def mapa_saude():
    # Use cache for farmacias data (5 minutes timeout)
    cache_key = "farmacias_map_data"
    farmacias_json = current_app.cache.get(cache_key)
    
    if farmacias_json is None:
        # Farmacia does not require coordinate columns. Read coordinates from
        # instances when an extended schema provides them and keep the map
        # usable with the existing address-only schema.
        farmacias = Farmacia.query.all()
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
                "nome": farmacia.nome_fantasia,
                "endereco": farmacia.endereco or "Endereço não informado",
                "cnpj": farmacia.cnpj,
                "responsavel": farmacia.responsavel,
                "lat": latitude,
                "lng": longitude,
                "tipo": "Farmácia",
            })
        
        farmacias_json = json.dumps(pontos, ensure_ascii=False)
        # Cache for 5 minutes (300 seconds)
        current_app.cache.set(cache_key, farmacias_json, timeout=300)

    api_key = os.environ.get("GOOGLE_MAPS_API_KEY", "")
    # Default coordinates for Sorocaba/SP
    return render_template("mapa.html", farmacias_json=farmacias_json, api_key=api_key, 
                          default_lat=-23.5015, default_lng=-47.4526)


@mapa_bp.route("/api/mapa/proximidade", methods=["POST"])
@login_required
def verificar_proximidade():
    """
    Verifica se o paciente está a menos de 1km de alguma farmácia parceira.
    Disciplina: Fundamentos de IoT - Cerca Virtual (Geofencing)
    
    Expected JSON payload:
    {
        "latitude": float,
        "longitude": float
    }
    """
    try:
        dados = request.get_json()
        
        if not dados:
            return resposta_erro("Dados não fornecidos", 400)
        
        paciente_lat = dados.get('latitude')
        paciente_lon = dados.get('longitude')
        
        if paciente_lat is None or paciente_lon is None:
            return resposta_erro("latitude e longitude são obrigatórios", 400)
        
        # Limite de proximidade em km (1km)
        LIMITE_PROXIMIDADE_KM = 1.0
        
        farmacias = Farmacia.query.all()
        farmacias_proximas = []
        
        for farmacia in farmacias:
            # Obtém coordenadas da farmácia (se não tiver, usa valores padrão de São Paulo)
            farmacia_lat = getattr(farmacia, 'latitude', -23.5505)
            farmacia_lon = getattr(farmacia, 'longitude', -46.6333)
            
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
        
        # Ordena por distância
        farmacias_proximas.sort(key=lambda f: f['distancia_km'])
        
        return resposta_ok({
            'farmacias_proximas': farmacias_proximas,
            'total': len(farmacias_proximas),
            'limite_km': LIMITE_PROXIMIDADE_KM,
            'alerta': len(farmacias_proximas) > 0,
            'mensagem': f'{len(farmacias_proximas)} farmácia(s) próxima(s) encontrada(s)' if farmacias_proximas else 'Nenhuma farmácia próxima encontrada'
        })
        
    except Exception as e:
        return resposta_erro(f"Erro ao verificar proximidade: {str(e)}", 500)
