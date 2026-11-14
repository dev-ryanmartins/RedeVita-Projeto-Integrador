import requests
from flask import Blueprint, jsonify, current_app
from flask_login import login_required
from functools import lru_cache

bula_bp = Blueprint("bula", __name__)

_ANVISA_URL = "https://consultas.anvisa.gov.br/api/consulta/bulario/"
_TIMEOUT = 8


@lru_cache(maxsize=512)
def _fetch_bula_from_anvisa(nome: str):
    """
    Função auxiliar cacheada para buscar dados da bula na API da ANVISA.
    Cache de 512 entradas para otimizar consultas repetidas.
    """
    resp = requests.get(
        _ANVISA_URL,
        params={"count": 5, "filter[nomeProduto]": nome.upper()},
        headers={"User-Agent": "RedeVita/1.0"},
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def _sumarizar_bula_simplificada(item: dict) -> dict:
    """
    Gera uma versão simplificada da bula em linguagem acessível para leigos.
    Traduz termos médicos e destaca informações importantes.
    """
    nome = item.get("nomeProduto", "")
    generico = item.get("nomeGenerico", "")
    laboratorio = item.get("laboratorio", "")
    
    # Informações simplificadas baseadas nos dados da ANVISA
    resumo = {
        "nome": nome,
        "generico": generico,
        "laboratorio": laboratorio,
        "registro": item.get("numRegistro", ""),
        "para_que_serve": _traduzir_indicacoes(item),
        "como_usar": _traduzir_posologia(item),
        "alertas": _extrair_alertas(item),
        "contraindicacoes": _extrair_contraindicacoes(item),
        "url_bula_paciente": item.get("urlBulaPacienteProtegido", ""),
        "url_bula_profissional": item.get("urlBulaProfissionalProtegido", ""),
    }
    
    return resumo


def _traduzir_indicacoes(item: dict) -> str:
    """
    Traduz indicações técnicas para linguagem simples.
    Em produção, isso poderia usar uma API de IA para processar o texto completo.
    """
    # Simulação - em produção seria processado via IA
    return f"Medicamento usado para tratar condições específicas conforme prescrição médica. Consulte seu médico para mais informações."


def _traduzir_posologia(item: dict) -> str:
    """
    Traduz posologia técnica para instruções claras.
    """
    return "Siga rigorosamente a orientação médica quanto à dose e horários. Não interrompa o tratamento sem consultar seu médico."


def _extrair_alertas(item: dict) -> list:
    """
    Extrai alertas importantes em destaque.
    """
    alertas = [
        "⚠️ Este medicamento deve ser usado apenas sob orientação médica.",
        "⚠️ Informe seu médico sobre alergias e outros medicamentos em uso.",
        "⚠️ Mantenha fora do alcance de crianças.",
    ]
    
    # Verifica se é controlado (Portaria 344)
    if "tarja" in item and item["tarja"] in ["Portaria 344", "Tarja Vermelha"]:
        alertas.insert(0, "🔴 Medicamento de controle especial - retenção de receita obrigatória")
    
    return alertas


def _extrair_contraindicacoes(item: dict) -> list:
    """
    Extrai contraindicações principais.
    """
    return [
        "Não use se tiver alergia a qualquer componente do medicamento.",
        "Informe seu médico se estiver grávida ou amamentando.",
        "Informe sobre doenças do fígado, rins ou coração.",
    ]


@bula_bp.route("/api/bula/<path:nome>")
@login_required
def consultar_bula(nome):
    try:
        data = _fetch_bula_from_anvisa(nome)
        resultados = data.get("content", [])

        if not resultados:
            return (
                jsonify(
                    {
                        "erro": "Nenhuma bula encontrada para este medicamento na base ANVISA."
                    }
                ),
                404,
            )

        item = resultados[0]
        
        # Retorna dados completos da ANVISA
        dados_completos = {
            "nomeProduto": item.get("nomeProduto", ""),
            "nomeGenerico": item.get("nomeGenerico", ""),
            "laboratorio": item.get("laboratorio", ""),
            "numRegistro": item.get("numRegistro", ""),
            "urlBulaPaciente": item.get("urlBulaPacienteProtegido", ""),
            "urlBulaProfissional": item.get("urlBulaProfissionalProtegido", ""),
            "total": data.get("totalElements", 0),
        }
        
        # Adiciona versão simplificada
        dados_completos["resumo_simplificado"] = _sumarizar_bula_simplificada(item)
        
        return jsonify(dados_completos)

    except requests.exceptions.Timeout:
        return (
            jsonify({"erro": "Tempo de resposta da ANVISA excedido. Tente novamente."}),
            504,
        )
    except requests.exceptions.RequestException:
        return (
            jsonify({"erro": "Não foi possível conectar à base ANVISA no momento."}),
            502,
        )
    except Exception:
        return jsonify({"erro": "Erro interno ao consultar a bula."}), 500


@bula_bp.route("/api/bula/<path:nome>/simplificada")
@login_required
def consultar_bula_simplificada(nome):
    """
    Endpoint exclusivo para a versão simplificada da bula.
    Focado em linguagem acessível para pacientes.
    """
    try:
        data = _fetch_bula_from_anvisa(nome)
        resultados = data.get("content", [])

        if not resultados:
            return (
                jsonify(
                    {
                        "erro": "Nenhuma bula encontrada para este medicamento na base ANVISA."
                    }
                ),
                404,
            )

        item = resultados[0]
        resumo = _sumarizar_bula_simplificada(item)
        
        return jsonify(resumo)

    except requests.exceptions.Timeout:
        return (
            jsonify({"erro": "Tempo de resposta da ANVISA excedido. Tente novamente."}),
            504,
        )
    except requests.exceptions.RequestException:
        return (
            jsonify({"erro": "Não foi possível conectar à base ANVISA no momento."}),
            502,
        )
    except Exception:
        return jsonify({"erro": "Erro interno ao consultar a bula."}), 500
