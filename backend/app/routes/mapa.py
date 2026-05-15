import os
import json
from flask import Blueprint, render_template
from flask_login import login_required
from app.models.farmacia import Farmacia

mapa_bp = Blueprint('mapa', __name__)


@mapa_bp.route('/mapa')
@login_required
def mapa_saude():
    farmacias = Farmacia.query.all()
    farmacias_json = json.dumps([
        {
            'id': f.id,
            'nome': f.nome_fantasia,
            'endereco': f.endereco,
            'cnpj': f.cnpj,
            'responsavel': f.responsavel
        }
        for f in farmacias
    ], ensure_ascii=False)

    api_key = os.environ.get('GOOGLE_MAPS_API_KEY', '')
    return render_template('mapa.html', farmacias_json=farmacias_json, api_key=api_key)
