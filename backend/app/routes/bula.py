import requests
from flask import Blueprint, jsonify
from flask_login import login_required

bula_bp = Blueprint('bula', __name__)

_ANVISA_URL = 'https://consultas.anvisa.gov.br/api/consulta/bulario/'
_TIMEOUT = 8


@bula_bp.route('/api/bula/<path:nome>')
@login_required
def consultar_bula(nome):
    try:
        resp = requests.get(
            _ANVISA_URL,
            params={'count': 5, 'filter[nomeProduto]': nome.upper()},
            headers={'User-Agent': 'RedeVita/1.0'},
            timeout=_TIMEOUT
        )
        resp.raise_for_status()
        data = resp.json()
        resultados = data.get('content', [])

        if not resultados:
            return jsonify({'erro': 'Nenhuma bula encontrada para este medicamento na base ANVISA.'}), 404

        item = resultados[0]
        return jsonify({
            'nomeProduto': item.get('nomeProduto', ''),
            'nomeGenerico': item.get('nomeGenerico', ''),
            'laboratorio': item.get('laboratorio', ''),
            'numRegistro': item.get('numRegistro', ''),
            'urlBulaPaciente': item.get('urlBulaPacienteProtegido', ''),
            'urlBulaProfissional': item.get('urlBulaProfissionalProtegido', ''),
            'total': data.get('totalElements', 0),
        })

    except requests.exceptions.Timeout:
        return jsonify({'erro': 'Tempo de resposta da ANVISA excedido. Tente novamente.'}), 504
    except requests.exceptions.RequestException:
        return jsonify({'erro': 'Não foi possível conectar à base ANVISA no momento.'}), 502
    except Exception:
        return jsonify({'erro': 'Erro interno ao consultar a bula.'}), 500
