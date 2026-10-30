"""
Blueprint do Laboratório de Crises da Cadeia Frio.

Este blueprint fornece uma área de treinamento para simular cenários de falha
na cadeia frio. Não cria, lê ou modifica dados reais no banco de dados.
Todas as leituras são sintéticas e identificadas como simulação.

Acesso: Admin e Farmacêutico
"""

from flask import Blueprint, render_template, request, jsonify
from app.core.decorators import farmaceutico_required
from app.core.api_responses import resposta_ok, resposta_erro, ERRO_VALIDACAO
from app.services.cold_crisis_simulator import ColdCrisisSimulator

cold_crisis_lab_bp = Blueprint('cold_crisis_lab', __name__)

# Limites de parâmetros
MAX_DURACAO_HORAS = 24
MIN_DURACAO_HORAS = 1
MAX_INTERVALO_MINUTOS = 60
MIN_INTERVALO_MINUTOS = 1


@cold_crisis_lab_bp.route('/laboratorio-crise-cadeia-frio', methods=['GET'])
@farmaceutico_required
def laboratorio_page():
    """
    Página do Laboratório de Crises da Cadeia Frio.

    Acesso: Admin e Farmacêutico
    """
    return render_template('cold_crisis_lab.html')


@cold_crisis_lab_bp.route('/api/laboratorio-crise-cadeia-frio/cenarios', methods=['GET'])
@farmaceutico_required
def listar_cenarios():
    """
    Lista os cenários de simulação disponíveis.

    Acesso: Admin e Farmacêutico
    """
    simulador = ColdCrisisSimulator()
    cenarios = simulador.listar_cenarios()

    return resposta_ok(dados={"cenarios": cenarios})


@cold_crisis_lab_bp.route('/api/laboratorio-crise-cadeia-frio/simular', methods=['POST'])
@farmaceutico_required
def simular_cenario():
    """
    Executa a simulação de um cenário específico.

    Parâmetros:
        cenario: Tipo do cenário (falha_energia, falha_rede, falha_sensor, recuperacao)
        duracao_horas: Duração do cenário em horas (1-24)
        intervalo_minutos: Intervalo entre leituras em minutos (1-60)
        seed: Seed para reprodutibilidade (opcional)

    Acesso: Admin e Farmacêutico
    """
    try:
        data = request.get_json()

        if not data:
            return resposta_erro(
                ERRO_VALIDACAO,
                "Corpo da requisição vazio",
                status=400
            )

        # Validar parâmetros
        cenario = data.get('cenario')
        if not cenario:
            return resposta_erro(
                ERRO_VALIDACAO,
                "Parâmetro 'cenario' é obrigatório",
                status=400
            )

        duracao_horas = data.get('duracao_horas', 6)
        intervalo_minutos = data.get('intervalo_minutos', 15)
        seed = data.get('seed')

        # Validar duração
        if not isinstance(duracao_horas, int) or duracao_horas < MIN_DURACAO_HORAS or duracao_horas > MAX_DURACAO_HORAS:
            return resposta_erro(
                ERRO_VALIDACAO,
                f"Duração deve ser entre {MIN_DURACAO_HORAS} e {MAX_DURACAO_HORAS} horas",
                status=400
            )

        # Validar intervalo
        if not isinstance(intervalo_minutos, int) or intervalo_minutos < MIN_INTERVALO_MINUTOS or intervalo_minutos > MAX_INTERVALO_MINUTOS:
            return resposta_erro(
                ERRO_VALIDACAO,
                f"Intervalo deve ser entre {MIN_INTERVALO_MINUTOS} e {MAX_INTERVALO_MINUTOS} minutos",
                status=400
            )

        # Validar seed
        if seed is not None and not isinstance(seed, int):
            return resposta_erro(
                ERRO_VALIDACAO,
                "Seed deve ser um número inteiro",
                status=400
            )

        # Executar simulação
        simulador = ColdCrisisSimulator(seed=seed)
        resultado = simulador.obter_cenario(
            tipo=cenario,
            duracao_horas=duracao_horas,
            intervalo_minutos=intervalo_minutos
        )

        return resposta_ok(dados=resultado)

    except ValueError as e:
        return resposta_erro(
            ERRO_VALIDACAO,
            str(e),
            status=400
        )
    except Exception as e:
        # Não expor detalhes internos em produção
        return resposta_erro(
            "SIMULATION_ERROR",
            "Erro ao executar simulação",
            status=500
        )
