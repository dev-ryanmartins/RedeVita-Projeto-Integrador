"""
Testes para o serviço ColdCrisisSimulator.

Testa:
- Cenários determinísticos
- Reprodutibilidade com seed
- Limites de parâmetros
- Estrutura de dados de saída
"""

import pytest
from datetime import datetime, timedelta
from app.services.cold_crisis_simulator import ColdCrisisSimulator


class TestColdCrisisSimulator:
    """Testa o serviço de simulação."""

    def test_inicializacao_com_seed(self):
        """Simulador deve inicializar com seed específica."""
        seed = 12345
        simulador = ColdCrisisSimulator(seed=seed)
        assert simulador.seed == seed

    def test_inicializacao_sem_seed(self):
        """Simulador deve inicializar com seed aleatória se não fornecida."""
        simulador = ColdCrisisSimulator()
        assert simulador.seed is not None
        assert isinstance(simulador.seed, int)

    def test_listar_cenarios(self):
        """Deve listar os 4 cenários disponíveis."""
        simulador = ColdCrisisSimulator()
        cenarios = simulador.listar_cenarios()

        assert len(cenarios) == 4
        ids = [c['id'] for c in cenarios]
        assert 'falha_energia' in ids
        assert 'falha_rede' in ids
        assert 'falha_sensor' in ids
        assert 'recuperacao' in ids

    def test_cenario_falha_energia_estrutura(self):
        """Cenário de falha de energia deve ter estrutura correta."""
        simulador = ColdCrisisSimulator(seed=12345)
        resultado = simulador.gerar_cenario_falha_energia(duracao_horas=6, intervalo_minutos=15)

        assert resultado['cenario'] == 'falha_energia'
        assert resultado['simulado'] is True
        assert 'inicio' in resultado
        assert 'fim' in resultado
        assert 'leituras' in resultado
        assert 'eventos' in resultado
        assert 'estatisticas' in resultado
        assert len(resultado['leituras']) > 0
        assert len(resultado['eventos']) > 0

    def test_cenario_falha_energia_eventos(self):
        """Cenário de falha de energia deve ter eventos específicos."""
        simulador = ColdCrisisSimulator(seed=12345)
        resultado = simulador.gerar_cenario_falha_energia(duracao_horas=6, intervalo_minutos=15)

        tipos_eventos = [e['tipo'] for e in resultado['eventos']]
        assert 'FALHA_ENERGIA' in tipos_eventos
        assert 'ENERGIA_RESTAURADA' in tipos_eventos

    def test_cenario_falha_rede_estrutura(self):
        """Cenário de falha de rede deve ter estrutura correta."""
        simulador = ColdCrisisSimulator(seed=12345)
        resultado = simulador.gerar_cenario_falha_rede(duracao_horas=4, intervalo_minutos=10)

        assert resultado['cenario'] == 'falha_rede'
        assert resultado['simulado'] is True
        assert 'leituras_pendentes' in resultado
        assert resultado['leituras_pendentes'] > 0

    def test_cenario_falha_rede_eventos(self):
        """Cenário de falha de rede deve ter eventos específicos."""
        simulador = ColdCrisisSimulator(seed=12345)
        resultado = simulador.gerar_cenario_falha_rede(duracao_horas=4, intervalo_minutos=10)

        tipos_eventos = [e['tipo'] for e in resultado['eventos']]
        assert 'FALHA_REDE' in tipos_eventos
        assert 'REDE_RESTAURADA' in tipos_eventos

    def test_cenario_falha_sensor_estrutura(self):
        """Cenário de falha de sensor deve ter estrutura correta."""
        simulador = ColdCrisisSimulator(seed=12345)
        resultado = simulador.gerar_cenario_falha_sensor(duracao_horas=5, intervalo_minutos=15)

        assert resultado['cenario'] == 'falha_sensor'
        assert resultado['simulado'] is True
        assert 'lacunas' in resultado

    def test_cenario_falha_sensor_eventos(self):
        """Cenário de falha de sensor deve ter eventos específicos."""
        simulador = ColdCrisisSimulator(seed=12345)
        resultado = simulador.gerar_cenario_falha_sensor(duracao_horas=5, intervalo_minutos=15)

        tipos_eventos = [e['tipo'] for e in resultado['eventos']]
        assert 'FALHA_SENSOR' in tipos_eventos
        assert 'SENSOR_SUBSTITUIDO' in tipos_eventos

    def test_cenario_recuperacao_estrutura(self):
        """Cenário de recuperação deve ter estrutura correta."""
        simulador = ColdCrisisSimulator(seed=12345)
        resultado = simulador.gerar_cenario_recuperacao(duracao_horas=8, intervalo_minutos=15)

        assert resultado['cenario'] == 'recuperacao'
        assert resultado['simulado'] is True

    def test_cenario_recuperacao_eventos(self):
        """Cenário de recuperação deve ter eventos específicos."""
        simulador = ColdCrisisSimulator(seed=12345)
        resultado = simulador.gerar_cenario_recuperacao(duracao_horas=8, intervalo_minutos=15)

        tipos_eventos = [e['tipo'] for e in resultado['eventos']]
        assert 'INICIO_RECUPERACAO' in tipos_eventos
        assert 'RECUPERACAO_COMPLETA' in tipos_eventos

    def test_leituras_simulado_flag(self):
        """Todas as leituras devem ter flag simulado=True."""
        simulador = ColdCrisisSimulator(seed=12345)
        resultado = simulador.gerar_cenario_falha_energia(duracao_horas=6, intervalo_minutos=15)

        for leitura in resultado['leituras']:
            assert leitura['simulado'] is True

    def test_eventos_simulado_flag(self):
        """Todos os eventos devem ter flag simulado=True."""
        simulador = ColdCrisisSimulator(seed=12345)
        resultado = simulador.gerar_cenario_falha_energia(duracao_horas=6, intervalo_minutos=15)

        for evento in resultado['eventos']:
            assert evento['simulado'] is True

    def test_estatisticas_calculadas(self):
        """Estatísticas devem ser calculadas corretamente."""
        simulador = ColdCrisisSimulator(seed=12345)
        resultado = simulador.gerar_cenario_falha_energia(duracao_horas=6, intervalo_minutos=15)

        stats = resultado['estatisticas']
        assert 'total_leituras' in stats
        assert 'temperatura_min' in stats
        assert 'temperatura_max' in stats
        assert 'temperatura_media' in stats
        assert 'umidade_min' in stats
        assert 'umidade_max' in stats
        assert 'umidade_media' in stats
        assert 'status_normal' in stats
        assert 'status_alerta' in stats
        assert 'status_critico' in stats
        assert 'status_frio' in stats

    def test_estatisticas_valores_consistentes(self):
        """Valores de estatísticas devem ser consistentes com leituras."""
        simulador = ColdCrisisSimulator(seed=12345)
        resultado = simulador.gerar_cenario_falha_energia(duracao_horas=6, intervalo_minutos=15)

        stats = resultado['estatisticas']
        leituras = resultado['leituras']

        assert stats['total_leituras'] == len(leituras)

        temps = [l['temperatura'] for l in leituras]
        assert stats['temperatura_min'] == min(temps)
        assert stats['temperatura_max'] == max(temps)

        umids = [l['umidade'] for l in leituras]
        assert stats['umidade_min'] == min(umids)
        assert stats['umidade_max'] == max(umids)

    def test_reprodutibilidade_mesma_seed(self):
        """Mesma seed deve produzir resultados idênticos."""
        seed = 12345

        simulador1 = ColdCrisisSimulator(seed=seed)
        resultado1 = simulador1.gerar_cenario_falha_energia(duracao_horas=6, intervalo_minutos=15)

        simulador2 = ColdCrisisSimulator(seed=seed)
        resultado2 = simulador2.gerar_cenario_falha_energia(duracao_horas=6, intervalo_minutos=15)

        # Mesmas temperaturas
        temps1 = [l['temperatura'] for l in resultado1['leituras']]
        temps2 = [l['temperatura'] for l in resultado2['leituras']]
        assert temps1 == temps2

    def test_reprodutibilidade_seeds_diferentes(self):
        """Seeds diferentes devem produzir resultados diferentes."""
        simulador1 = ColdCrisisSimulator(seed=12345)
        resultado1 = simulador1.gerar_cenario_falha_energia(duracao_horas=6, intervalo_minutos=15)

        simulador2 = ColdCrisisSimulator(seed=54321)
        resultado2 = simulador2.gerar_cenario_falha_energia(duracao_horas=6, intervalo_minutos=15)

        # Temperaturas diferentes
        temps1 = [l['temperatura'] for l in resultado1['leituras']]
        temps2 = [l['temperatura'] for l in resultado2['leituras']]
        assert temps1 != temps2

    def test_obter_cenario_via_metodo(self):
        """Método obter_cenario deve funcionar corretamente."""
        simulador = ColdCrisisSimulator(seed=12345)
        resultado = simulador.obter_cenario(
            tipo='falha_energia',
            duracao_horas=6,
            intervalo_minutos=15
        )

        assert resultado['cenario'] == 'falha_energia'
        assert resultado['simulado'] is True

    def test_obter_cenario_invalido_erro(self):
        """Cenário inválido deve levantar ValueError."""
        simulador = ColdCrisisSimulator(seed=12345)

        with pytest.raises(ValueError) as exc_info:
            simulador.obter_cenario(tipo='cenario_invalido')

        assert 'Cenário não reconhecido' in str(exc_info.value)

    def test_limites_temperatura(self):
        """Temperaturas devem estar dentro dos limites definidos."""
        simulador = ColdCrisisSimulator(seed=12345)
        resultado = simulador.gerar_cenario_falha_energia(duracao_horas=6, intervalo_minutos=15)

        for leitura in resultado['leituras']:
            assert 0.0 <= leitura['temperatura'] <= 15.0

    def test_limites_umidade(self):
        """Umidades devem estar dentro dos limites definidos."""
        simulador = ColdCrisisSimulator(seed=12345)
        resultado = simulador.gerar_cenario_falha_energia(duracao_horas=6, intervalo_minutos=15)

        for leitura in resultado['leituras']:
            assert 30.0 <= leitura['umidade'] <= 70.0

    def test_status_leituras(self):
        """Status das leituras deve ser um dos valores válidos."""
        simulador = ColdCrisisSimulator(seed=12345)
        resultado = simulador.gerar_cenario_falha_energia(duracao_horas=6, intervalo_minutos=15)

        status_validos = ['NORMAL', 'ALERTA', 'CRÍTICO', 'FRIO']
        for leitura in resultado['leituras']:
            assert leitura['status'] in status_validos

    def test_timestamps_validos(self):
        """Timestamps devem ser datas ISO válidas."""
        simulador = ColdCrisisSimulator(seed=12345)
        resultado = simulador.gerar_cenario_falha_energia(duracao_horas=6, intervalo_minutos=15)

        # Timestamps de início e fim
        inicio = datetime.fromisoformat(resultado['inicio'])
        fim = datetime.fromisoformat(resultado['fim'])
        assert fim > inicio

        # Timestamps das leituras
        for leitura in resultado['leituras']:
            timestamp = datetime.fromisoformat(leitura['timestamp'])
            assert inicio <= timestamp <= fim

    def test_duracao_diferente_gera_diferente_quantidade(self):
        """Duração diferente deve gerar quantidade diferente de leituras."""
        simulador = ColdCrisisSimulator(seed=12345)

        resultado1 = simulador.gerar_cenario_falha_energia(duracao_horas=3, intervalo_minutos=15)
        resultado2 = simulador.gerar_cenario_falha_energia(duracao_horas=6, intervalo_minutos=15)

        assert len(resultado2['leituras']) > len(resultado1['leituras'])

    def test_intervalo_diferente_gera_diferente_quantidade(self):
        """Intervalo diferente deve gerar quantidade diferente de leituras."""
        simulador = ColdCrisisSimulator(seed=12345)

        resultado1 = simulador.gerar_cenario_falha_energia(duracao_horas=6, intervalo_minutos=30)
        resultado2 = simulador.gerar_cenario_falha_energia(duracao_horas=6, intervalo_minutos=15)

        assert len(resultado2['leituras']) > len(resultado1['leituras'])
