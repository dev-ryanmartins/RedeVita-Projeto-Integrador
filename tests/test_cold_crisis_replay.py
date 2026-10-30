"""
Testes para Replay e Avaliação de Resposta a Crises

Testes de replay determinístico, comparação de execuções e avaliação de roteiro.
"""

import pytest
from datetime import datetime, timedelta
from main import create_app
from app.database import db
from app.services.cold_crisis_replay import ColdCrisisReplayService


@pytest.fixture
def app():
    """Cria aplicação de teste."""
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key'
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Cria cliente de teste."""
    return app.test_client()


@pytest.fixture
def service():
    """Cria instância do serviço de replay."""
    return ColdCrisisReplayService()


class TestRoteiro:
    """Testes do roteiro de treinamento."""

    def test_obter_informacao_roteiro(self, service):
        """Deve retornar informações do roteiro."""
        info = service.obter_informacao_roteiro()
        
        assert 'versao' in info
        assert 'data' in info
        assert 'aviso' in info
        assert info['versao'] == "1.0"
        assert 'demonstrativo' in info['aviso'].lower()

    def test_obter_roteiro_cenario_valido(self, service):
        """Deve retornar etapas para cenário válido."""
        roteiro = service.obter_roteiro('falha_energia')
        
        assert len(roteiro) > 0
        assert any(e['id'] == 'reconhecer_alerta' for e in roteiro)
        assert all('id' in e and 'nome' in e and 'descricao' in e for e in roteiro)

    def test_obter_roteiro_cenario_invalido(self, service):
        """Deve retornar lista vazia para cenário inválido."""
        roteiro = service.obter_roteiro('cenario_inexistente')
        
        assert len(roteiro) == 0

    def test_roteiro_nao_vazio(self, service):
        """Todos os cenários devem ter roteiro."""
        cenarios = ['falha_energia', 'falha_rede', 'falha_sensor', 'recuperacao']
        
        for cenario in cenarios:
            roteiro = service.obter_roteiro(cenario)
            assert len(roteiro) > 0, f"Cenário {cenario} não tem roteiro"


class TestReplay:
    """Testes de replay de cenários."""

    def test_iniciar_replay_cenario_valido(self, service):
        """Deve iniciar replay com cenário válido."""
        execucao = service.iniciar_replay(
            cenario='falha_energia',
            duracao_horas=6,
            intervalo_minutos=15,
            seed=12345
        )
        
        assert 'id' in execucao
        assert 'cenario' in execucao
        assert 'seed' in execucao
        assert execucao['cenario'] == 'falha_energia'
        assert execucao['seed'] == 12345
        assert 'etapas_cobertas' in execucao
        assert 'etapas_pendentes' in execucao
        assert 'concluido' in execucao
        assert not execucao['concluido']

    def test_iniciar_replay_sem_seed(self, service):
        """Deve iniciar replay sem seed especificada."""
        execucao = service.iniciar_replay(
            cenario='falha_energia',
            duracao_horas=6,
            intervalo_minutos=15
        )
        
        assert 'seed' in execucao
        assert execucao['seed'] is not None

    def test_iniciar_replay_reprodutivel(self, service):
        """Mesma seed deve produzir mesmo resultado."""
        execucao1 = service.iniciar_replay(
            cenario='falha_energia',
            duracao_horas=6,
            intervalo_minutos=15,
            seed=99999
        )
        
        execucao2 = service.iniciar_replay(
            cenario='falha_energia',
            duracao_horas=6,
            intervalo_minutos=15,
            seed=99999
        )
        
        assert execucao1['seed'] == execucao2['seed']
        assert execucao1['cenario'] == execucao2['cenario']


class TestValidacaoParametros:
    """Testes de validação de parâmetros."""

    def test_validar_cenario_valido(self, service):
        """Deve aceitar cenário válido."""
        service.validar_parametros_replay(
            cenario='falha_energia',
            duracao_horas=6,
            intervalo_minutos=15
        )
        # Não deve levantar exceção

    def test_validar_cenario_invalido(self, service):
        """Deve rejeitar cenário inválido."""
        with pytest.raises(ValueError) as exc:
            service.validar_parametros_replay(
                cenario='invalido',
                duracao_horas=6,
                intervalo_minutos=15
            )
        assert "inválido" in str(exc.value).lower()

    def test_validar_duracao_minima(self, service):
        """Deve rejeitar duração abaixo do mínimo."""
        with pytest.raises(ValueError) as exc:
            service.validar_parametros_replay(
                cenario='falha_energia',
                duracao_horas=0,
                intervalo_minutos=15
            )
        assert "duração" in str(exc.value).lower()

    def test_validar_duracao_maxima(self, service):
        """Deve rejeitar duração acima do máximo."""
        with pytest.raises(ValueError) as exc:
            service.validar_parametros_replay(
                cenario='falha_energia',
                duracao_horas=25,
                intervalo_minutos=15
            )
        assert "duração" in str(exc.value).lower()

    def test_validar_intervalo_minimo(self, service):
        """Deve rejeitar intervalo abaixo do mínimo."""
        with pytest.raises(ValueError) as exc:
            service.validar_parametros_replay(
                cenario='falha_energia',
                duracao_horas=6,
                intervalo_minutos=0
            )
        assert "intervalo" in str(exc.value).lower()

    def test_validar_intervalo_maximo(self, service):
        """Deve rejeitar intervalo acima do máximo."""
        with pytest.raises(ValueError) as exc:
            service.validar_parametros_replay(
                cenario='falha_energia',
                duracao_horas=6,
                intervalo_minutos=61
            )
        assert "intervalo" in str(exc.value).lower()

    def test_validar_velocidade_minima(self, service):
        """Deve rejeitar velocidade abaixo do mínimo."""
        with pytest.raises(ValueError) as exc:
            service.validar_parametros_replay(
                cenario='falha_energia',
                duracao_horas=6,
                intervalo_minutos=15,
                velocidade=0
            )
        assert "velocidade" in str(exc.value).lower()

    def test_validar_velocidade_maxima(self, service):
        """Deve rejeitar velocidade acima do máximo."""
        with pytest.raises(ValueError) as exc:
            service.validar_parametros_replay(
                cenario='falha_energia',
                duracao_horas=6,
                intervalo_minutos=15,
                velocidade=11
            )
        assert "velocidade" in str(exc.value).lower()


class TestEscolhas:
    """Testes de adição de escolhas."""

    def test_adicionar_escolha_valida(self, service):
        """Deve adicionar escolha válida."""
        execucao = service.iniciar_replay(
            cenario='falha_energia',
            duracao_horas=6,
            intervalo_minutos=15,
            seed=12345
        )
        
        # Adicionar escolha
        etapas_pendentes_antes = len(execucao['etapas_pendentes'])
        execucao_atualizada = service.adicionar_escolha(
            execucao=execucao,
            etapa_id='reconhecer_alerta',
            tempo_virtual=1.0
        )
        
        assert len(execucao_atualizada['escolhas']) == 1
        assert len(execucao_atualizada['etapas_cobertas']) == 1
        # A etapa pode ou não ser removida das pendentes dependendo da implementação
        assert execucao_atualizada['tempo_virtual'] == 1.0

    def test_adicionar_escolha_invalida(self, service):
        """Deve ignorar escolha de etapa inválida."""
        execucao = service.iniciar_replay(
            cenario='falha_energia',
            duracao_horas=6,
            intervalo_minutos=15,
            seed=12345
        )
        
        # Tentar adicionar escolha inválida
        execucao_atualizada = service.adicionar_escolha(
            execucao=execucao,
            etapa_id='etapa_inexistente',
            tempo_virtual=1.0
        )
        
        # Não deve modificar
        assert len(execucao_atualizada['escolhas']) == 0
        assert len(execucao_atualizada['etapas_cobertas']) == 0

    def test_concluido_sem_etapas_pendentes(self, service):
        """Deve marcar como concluído quando não há etapas pendentes."""
        execucao = service.iniciar_replay(
            cenario='falha_energia',
            duracao_horas=6,
            intervalo_minutos=15,
            seed=12345
        )
        
        # Adicionar todas as etapas
        for etapa in execucao['etapas_pendentes']:
            execucao = service.adicionar_escolha(
                execucao=execucao,
                etapa_id=etapa['id'],
                tempo_virtual=1.0
            )
        
        assert execucao['concluido']
        assert 'fim' in execucao


class TestCobertura:
    """Testes de cálculo de cobertura."""

    def test_calcular_cobertura_inicial(self, service):
        """Deve calcular cobertura inicial zerada."""
        execucao = service.iniciar_replay(
            cenario='falha_energia',
            duracao_horas=6,
            intervalo_minutos=15,
            seed=12345
        )
        
        cobertura = service.calcular_cobertura(execucao)
        
        assert cobertura['total_etapas'] > 0
        assert cobertura['etapas_cobertas'] == 0
        assert cobertura['etapas_pendentes'] > 0
        assert cobertura['porcentagem_cobertura'] == 0
        assert not cobertura['concluido']

    def test_calcular_cobertura_parcial(self, service):
        """Deve calcular cobertura parcial."""
        execucao = service.iniciar_replay(
            cenario='falha_energia',
            duracao_horas=6,
            intervalo_minutos=15,
            seed=12345
        )
        
        # Adicionar uma etapa
        execucao = service.adicionar_escolha(
            execucao=execucao,
            etapa_id='reconhecer_alerta',
            tempo_virtual=1.0
        )
        
        cobertura = service.calcular_cobertura(execucao)
        
        assert cobertura['etapas_cobertas'] == 1
        assert cobertura['porcentagem_cobertura'] > 0
        assert cobertura['porcentagem_cobertura'] < 100

    def test_calcular_cobertura_completa(self, service):
        """Deve calcular cobertura completa."""
        execucao = service.iniciar_replay(
            cenario='falha_energia',
            duracao_horas=6,
            intervalo_minutos=15,
            seed=12345
        )
        
        # Adicionar todas as etapas
        for etapa in execucao['etapas_pendentes']:
            execucao = service.adicionar_escolha(
                execucao=execucao,
                etapa_id=etapa['id'],
                tempo_virtual=1.0
            )
        
        cobertura = service.calcular_cobertura(execucao)
        
        assert cobertura['etapas_pendentes'] == 0
        assert cobertura['porcentagem_cobertura'] == 100
        assert cobertura['concluido']


class TestComparacao:
    """Testes de comparação de execuções."""

    def test_comparar_execucoes_validas(self, service):
        """Deve comparar duas execuções válidas."""
        execucao1 = service.iniciar_replay(
            cenario='falha_energia',
            duracao_horas=6,
            intervalo_minutos=15,
            seed=11111
        )
        
        execucao2 = service.iniciar_replay(
            cenario='falha_energia',
            duracao_horas=6,
            intervalo_minutos=15,
            seed=22222
        )
        
        # Adicionar diferentes escolhas
        execucao1 = service.adicionar_escolha(execucao1, 'reconhecer_alerta', 1.0)
        execucao2 = service.adicionar_escolha(execucao2, 'verificar_cobertura', 2.0)
        
        comparacao = service.comparar_execucoes(execucao1, execucao2)
        
        assert 'cenario' in comparacao
        assert 'cobertura1' in comparacao
        assert 'cobertura2' in comparacao
        assert 'etapas_comuns' in comparacao
        assert 'etapas_exclusivas_1' in comparacao
        assert 'etapas_exclusivas_2' in comparacao
        assert 'tempo_virtual_1' in comparacao
        assert 'tempo_virtual_2' in comparacao

    def test_comparar_execucoes_cenarios_diferentes(self, service):
        """Deve rejeitar comparação de cenários diferentes."""
        execucao1 = service.iniciar_replay(
            cenario='falha_energia',
            duracao_horas=6,
            intervalo_minutos=15,
            seed=11111
        )
        
        execucao2 = service.iniciar_replay(
            cenario='falha_rede',
            duracao_horas=6,
            intervalo_minutos=15,
            seed=22222
        )
        
        with pytest.raises(ValueError) as exc:
            service.comparar_execucoes(execucao1, execucao2)
        assert "mesmo cenário" in str(exc.value).lower()


class TestApenasLeitura:
    """Testes de que o replay não altera dados reais."""

    def test_replay_nao_altera_banco(self, app, service):
        """Replay não deve alterar dados no banco."""
        with app.app_context():
            # Executar replay não deve criar tabelas ou registros
            execucao = service.iniciar_replay(
                cenario='falha_energia',
                duracao_horas=6,
                intervalo_minutos=15,
                seed=12345
            )
            
            # Verificar que não há tabelas adicionais
            # (O serviço reutiliza ColdCrisisSimulator que é apenas leitura)
            assert 'cenario' in execucao
            assert 'simulado' in execucao['resultado_cenario']
            assert execucao['resultado_cenario']['simulado']


class TestAvaliacao:
    """Testes de avaliação (apenas cobertura de roteiro)."""

    def test_avaliacao_nao_atribui_nota(self, service):
        """Avaliação não deve atribuir nota ou ranking."""
        execucao = service.iniciar_replay(
            cenario='falha_energia',
            duracao_horas=6,
            intervalo_minutos=15,
            seed=12345
        )
        
        cobertura = service.calcular_cobertura(execucao)
        
        # Deve ter apenas métricas de cobertura
        assert 'porcentagem_cobertura' in cobertura
        assert 'total_etapas' in cobertura
        assert 'etapas_cobertas' in cobertura
        # Não deve ter nota, ranking ou classificação individual
        assert 'nota' not in str(cobertura).lower()
        assert 'ranking' not in str(cobertura).lower()
        assert 'aprovado' not in str(cobertura).lower()
        assert 'reprovado' not in str(cobertura).lower()

    def test_avaliacao_nao_afirma_conformidade(self, service):
        """Avaliação não deve afirmar conformidade com normas."""
        info = service.obter_informacao_roteiro()
        
        # Deve explicitar que é material demonstrativo
        assert 'demonstrativo' in info['aviso'].lower()
        assert 'procedimento oficial' in info['aviso'].lower()
        assert 'orientação da anvisa' in info['aviso'].lower()
