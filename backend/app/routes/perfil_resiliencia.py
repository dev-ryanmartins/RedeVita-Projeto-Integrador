"""
Blueprint do Perfil de Resiliência da Farmácia Parceira.

NOTA: Esta funcionalidade depende da tabela perfis_resiliencia_farmacia,
que requer migration não implementada devido a bloqueio no ambiente atual.
O serviço retorna dados de demonstração para fins de validação.
"""

from flask import Blueprint, render_template, request, jsonify
from app.core.decorators import admin_required
from app.core.api_responses import resposta_ok, resposta_erro, ERRO_VALIDACAO
from app.services.perfil_resiliencia import PerfilResilienciaService

perfil_resiliencia_bp = Blueprint('perfil_resiliencia', __name__)


@perfil_resiliencia_bp.route('/perfil-resiliencia-farmacia', methods=['GET'])
@admin_required
def perfil_page():
    """
    Página do Perfil de Resiliência da Farmácia Parceira.

    Acesso: Admin apenas
    """
    return render_template('perfil_resiliencia.html')


@perfil_resiliencia_bp.route('/api/perfil-resiliencia/todos', methods=['GET'])
@admin_required
def listar_todos():
    """
    Lista todos os perfis de resiliência.

    Acesso: Admin apenas
    """
    try:
        service = PerfilResilienciaService()
        perfis = service.obter_todos_perfis()
        return resposta_ok(dados={"perfis": perfis})
    except Exception as e:
        return resposta_erro(
            "Erro ao listar perfis",
            status=500
        )


@perfil_resiliencia_bp.route('/api/perfil-resiliencia/farmacia/<int:farmacia_id>', methods=['GET'])
@admin_required
def obter_perfil(farmacia_id):
    """
    Obtém o perfil de resiliência de uma farmácia específica.

    Acesso: Admin apenas
    """
    try:
        service = PerfilResilienciaService()
        perfil = service.obter_perfil_por_farmacia(farmacia_id)
        
        if not perfil:
            return resposta_erro(
                ERRO_VALIDACAO,
                "Farmácia não encontrada",
                status=404
            )
        
        return resposta_ok(dados=perfil)
    except Exception as e:
        return resposta_erro(
            "Erro ao obter perfil",
            status=500
        )


@perfil_resiliencia_bp.route('/api/perfil-resiliencia/farmacia/<int:farmacia_id>', methods=['POST'])
@admin_required
def criar_perfil(farmacia_id):
    """
    Cria um novo perfil de resiliência.

    Acesso: Admin apenas
    """
    try:
        data = request.get_json()
        
        if not data:
            return resposta_erro(
                ERRO_VALIDACAO,
                "Corpo da requisição vazio",
                status=400
            )
        
        from flask_login import current_user
        service = PerfilResilienciaService()
        perfil = service.criar_perfil(farmacia_id, data, current_user.id)
        
        return resposta_ok(dados=perfil)
    except ValueError as e:
        return resposta_erro(
            ERRO_VALIDACAO,
            str(e),
            status=400
        )
    except Exception as e:
        return resposta_erro(
            "Erro ao criar perfil",
            status=500
        )


@perfil_resiliencia_bp.route('/api/perfil-resiliencia/farmacia/<int:farmacia_id>', methods=['PUT'])
@admin_required
def atualizar_perfil(farmacia_id):
    """
    Atualiza um perfil de resiliência existente.

    Acesso: Admin apenas
    """
    try:
        data = request.get_json()
        
        if not data:
            return resposta_erro(
                ERRO_VALIDACAO,
                "Corpo da requisição vazio",
                status=400
            )
        
        from flask_login import current_user
        service = PerfilResilienciaService()
        perfil = service.atualizar_perfil(farmacia_id, data, current_user.id)
        
        return resposta_ok(dados=perfil)
    except ValueError as e:
        return resposta_erro(
            ERRO_VALIDACAO,
            str(e),
            status=400
        )
    except Exception as e:
        return resposta_erro(
            "Erro ao atualizar perfil",
            status=500
        )


@perfil_resiliencia_bp.route('/api/perfil-resiliencia/farmacia/<int:farmacia_id>/iot', methods=['GET'])
@admin_required
def obter_iot(farmacia_id):
    """
    Obtém a última leitura IoT de uma farmácia.

    Acesso: Admin apenas
    """
    try:
        service = PerfilResilienciaService()
        leitura = service.obter_ultima_leitura_iot(farmacia_id)
        
        if not leitura:
            return resposta_ok(dados={"mensagem": "Sem dados recentes suficientes"})
        
        return resposta_ok(dados=leitura)
    except Exception as e:
        return resposta_erro(
            "Erro ao obter dados IoT",
            status=500
        )
