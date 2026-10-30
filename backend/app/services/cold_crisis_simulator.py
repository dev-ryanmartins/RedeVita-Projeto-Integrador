"""
Serviço de simulação de crises da cadeia frio.

Este serviço gera cenários determinísticos de falha na cadeia frio para treinamento.
Não cria, lê ou modifica dados reais no banco de dados.
Todas as leituras são sintéticas e identificadas como simulação.

Cenários:
- falha_energia: Falha de energia com aumento gradual de temperatura
- falha_rede: Indisponibilidade de rede com leituras pendentes
- falha_sensor: Falha ou interrupção de um sensor com lacunas
- recuperacao: Recuperação do ambiente após restabelecimento
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import random


class ColdCrisisSimulator:
    """Simulador de crises da cadeia frio com cenários determinísticos."""

    # Limites de temperatura para simulação (apenas demonstração, não regulatório)
    TEMPERATURA_MIN = 0.0
    TEMPERATURA_MAX = 15.0
    TEMPERATURA_IDEAL_MIN = 2.0
    TEMPERATURA_IDEAL_MAX = 8.0
    TEMPERATURA_ALERTA_MAX = 10.0

    # Limites de umidade para simulação
    UMIDADE_MIN = 30.0
    UMIDADE_MAX = 70.0
    UMIDADE_IDEAL_MIN = 40.0
    UMIDADE_IDEAL_MAX = 60.0

    def __init__(self, seed: Optional[int] = None):
        """
        Inicializa o simulador com uma seed para reprodutibilidade.

        Args:
            seed: Seed para gerador de números aleatórios. Se None, usa timestamp.
        """
        if seed is None:
            seed = int(datetime.now().timestamp())
        self.seed = seed
        self._rng = random.Random(seed)

    def _generate_reading(
        self,
        timestamp: datetime,
        temperatura_base: float,
        umidade_base: float,
        variacao_temp: float = 0.0,
        variacao_umid: float = 0.0,
        dispositivo_id: str = "SENSOR-001"
    ) -> Dict[str, Any]:
        """
        Gera uma leitura sintética com variação.

        Args:
            timestamp: Timestamp da leitura
            temperatura_base: Temperatura base
            umidade_base: Umidade base
            variacao_temp: Variação de temperatura
            variacao_umid: Variação de umidade
            dispositivo_id: Identificador do dispositivo

        Returns:
            Dicionário com leitura sintética
        """
        temperatura = temperatura_base + variacao_temp + self._rng.uniform(-0.5, 0.5)
        umidade = umidade_base + variacao_umid + self._rng.uniform(-2.0, 2.0)

        # Limitar valores
        temperatura = max(self.TEMPERATURA_MIN, min(self.TEMPERATURA_MAX, temperatura))
        umidade = max(self.UMIDADE_MIN, min(self.UMIDADE_MAX, umidade))

        # Determinar status
        if temperatura < self.TEMPERATURA_IDEAL_MIN:
            status = "FRIO"
        elif temperatura > self.TEMPERATURA_ALERTA_MAX:
            status = "CRÍTICO"
        elif temperatura > self.TEMPERATURA_IDEAL_MAX:
            status = "ALERTA"
        else:
            status = "NORMAL"

        return {
            "timestamp": timestamp.isoformat(),
            "temperatura": round(temperatura, 2),
            "umidade": round(umidade, 1),
            "dispositivo_id": dispositivo_id,
            "status": status,
            "simulado": True
        }

    def _generate_event(
        self,
        timestamp: datetime,
        tipo: str,
        descricao: str
    ) -> Dict[str, Any]:
        """
        Gera um evento simulado.

        Args:
            timestamp: Timestamp do evento
            tipo: Tipo do evento
            descricao: Descrição do evento

        Returns:
            Dicionário com evento simulado
        """
        return {
            "timestamp": timestamp.isoformat(),
            "tipo": tipo,
            "descricao": descricao,
            "simulado": True
        }

    def gerar_cenario_falha_energia(
        self,
        duracao_horas: int = 6,
        intervalo_minutos: int = 15
    ) -> Dict[str, Any]:
        """
        Gera cenário de falha de energia com aumento gradual de temperatura.

        O cenário simula:
        - Período normal antes da falha
        - Falha de energia e aumento de temperatura
        - Recuperação após retorno da energia

        Args:
            duracao_horas: Duração total do cenário em horas
            intervalo_minutos: Intervalo entre leituras em minutos

        Returns:
            Dicionário com cenário completo
        """
        inicio = datetime.now() - timedelta(hours=duracao_horas)
        falha_inicio = inicio + timedelta(hours=1)
        falha_fim = falha_inicio + timedelta(hours=3)
        fim = inicio + timedelta(hours=duracao_horas)

        leituras = []
        eventos = []
        timestamp = inicio

        # Período normal antes da falha
        while timestamp < falha_inicio:
            leitura = self._generate_reading(
                timestamp=timestamp,
                temperatura_base=5.0,
                umidade_base=50.0
            )
            leituras.append(leitura)
            timestamp += timedelta(minutes=intervalo_minutos)

        # Evento de falha de energia
        eventos.append(self._generate_event(
            timestamp=falha_inicio,
            tipo="FALHA_ENERGIA",
            descricao="Falha de energia detectada - sistema de refrigeração interrompido"
        ))

        # Período de falha - temperatura subindo gradualmente
        tempo_falha = 0
        while timestamp < falha_fim:
            # Temperatura sobe gradualmente (0.5°C por hora)
            variacao_temp = tempo_falha * 0.5
            leitura = self._generate_reading(
                timestamp=timestamp,
                temperatura_base=5.0,
                umidade_base=50.0,
                variacao_temp=variacao_temp
            )
            leituras.append(leitura)
            timestamp += timedelta(minutes=intervalo_minutos)
            tempo_falha += intervalo_minutos / 60.0

        # Evento de retorno da energia
        eventos.append(self._generate_event(
            timestamp=falha_fim,
            tipo="ENERGIA_RESTAURADA",
            descricao="Energia restaurada - sistema de refrigeração reiniciado"
        ))

        # Período de recuperação
        while timestamp < fim:
            # Temperatura volta ao normal gradualmente
            tempo_recuperacao = (timestamp - falha_fim).total_seconds() / 3600.0
            variacao_temp = max(0, 3.0 - tempo_recuperacao)
            leitura = self._generate_reading(
                timestamp=timestamp,
                temperatura_base=5.0,
                umidade_base=50.0,
                variacao_temp=variacao_temp
            )
            leituras.append(leitura)
            timestamp += timedelta(minutes=intervalo_minutos)

        return {
            "cenario": "falha_energia",
            "descricao": "Falha de energia com aumento gradual de temperatura",
            "inicio": inicio.isoformat(),
            "fim": fim.isoformat(),
            "leituras": leituras,
            "eventos": eventos,
            "estatisticas": self._calcular_estatisticas(leituras),
            "simulado": True
        }

    def gerar_cenario_falha_rede(
        self,
        duracao_horas: int = 4,
        intervalo_minutos: int = 10
    ) -> Dict[str, Any]:
        """
        Gera cenário de indisponibilidade de rede com leituras pendentes.

        O cenário simula:
        - Período normal com transmissão
        - Falha de rede com leituras acumuladas localmente
        - Retorno da rede e envio de leituras pendentes

        Args:
            duracao_horas: Duração total do cenário em horas
            intervalo_minutos: Intervalo entre leituras em minutos

        Returns:
            Dicionário com cenário completo
        """
        inicio = datetime.now() - timedelta(hours=duracao_horas)
        falha_inicio = inicio + timedelta(hours=1)
        falha_fim = falha_inicio + timedelta(hours=2)
        fim = inicio + timedelta(hours=duracao_horas)

        leituras = []
        eventos = []
        leituras_pendentes = []
        timestamp = inicio

        # Período normal com transmissão
        while timestamp < falha_inicio:
            leitura = self._generate_reading(
                timestamp=timestamp,
                temperatura_base=5.0,
                umidade_base=50.0
            )
            leitura["transmitido"] = True
            leituras.append(leitura)
            timestamp += timedelta(minutes=intervalo_minutos)

        # Evento de falha de rede
        eventos.append(self._generate_event(
            timestamp=falha_inicio,
            tipo="FALHA_REDE",
            descricao="Falha de rede detectada - leituras serão armazenadas localmente"
        ))

        # Período de falha - leituras acumuladas
        while timestamp < falha_fim:
            leitura = self._generate_reading(
                timestamp=timestamp,
                temperatura_base=5.0,
                umidade_base=50.0
            )
            leitura["transmitido"] = False
            leituras_pendentes.append(leitura)
            timestamp += timedelta(minutes=intervalo_minutos)

        # Evento de retorno da rede
        eventos.append(self._generate_event(
            timestamp=falha_fim,
            tipo="REDE_RESTAURADA",
            descricao=f"Rede restaurada - {len(leituras_pendentes)} leituras pendentes enviadas"
        ))

        # Período de recuperação - leituras pendentes enviadas
        for leitura in leituras_pendentes:
            leitura["transmitido"] = True
            leitura["enviado_em"] = falha_fim.isoformat()
            leituras.append(leitura)

        # Período normal após recuperação
        while timestamp < fim:
            leitura = self._generate_reading(
                timestamp=timestamp,
                temperatura_base=5.0,
                umidade_base=50.0
            )
            leitura["transmitido"] = True
            leituras.append(leitura)
            timestamp += timedelta(minutes=intervalo_minutos)

        return {
            "cenario": "falha_rede",
            "descricao": "Indisponibilidade de rede com leituras pendentes",
            "inicio": inicio.isoformat(),
            "fim": fim.isoformat(),
            "leituras": leituras,
            "eventos": eventos,
            "leituras_pendentes": len(leituras_pendentes),
            "estatisticas": self._calcular_estatisticas(leituras),
            "simulado": True
        }

    def gerar_cenario_falha_sensor(
        self,
        duracao_horas: int = 5,
        intervalo_minutos: int = 15
    ) -> Dict[str, Any]:
        """
        Gera cenário de falha de sensor com lacunas na série de leituras.

        O cenário simula:
        - Período normal com leituras regulares
        - Falha do sensor com lacunas nos dados
        - Substituição do sensor e retorno das leituras

        Args:
            duracao_horas: Duração total do cenário em horas
            intervalo_minutos: Intervalo entre leituras em minutos

        Returns:
            Dicionário com cenário completo
        """
        inicio = datetime.now() - timedelta(hours=duracao_horas)
        falha_inicio = inicio + timedelta(hours=1)
        falha_fim = falha_inicio + timedelta(hours=2)
        fim = inicio + timedelta(hours=duracao_horas)

        leituras = []
        eventos = []
        timestamp = inicio

        # Período normal
        while timestamp < falha_inicio:
            leitura = self._generate_reading(
                timestamp=timestamp,
                temperatura_base=5.0,
                umidade_base=50.0,
                dispositivo_id="SENSOR-001"
            )
            leituras.append(leitura)
            timestamp += timedelta(minutes=intervalo_minutos)

        # Evento de falha do sensor
        eventos.append(self._generate_event(
            timestamp=falha_inicio,
            tipo="FALHA_SENSOR",
            descricao="Falha no sensor SENSOR-001 detectada - leituras interrompidas"
        ))

        # Período de falha - lacunas nos dados
        while timestamp < falha_fim:
            # Apenas algumas leituras durante a falha (intermitente)
            if self._rng.random() < 0.2:  # 20% de chance de leitura
                leitura = self._generate_reading(
                    timestamp=timestamp,
                    temperatura_base=5.0,
                    umidade_base=50.0,
                    dispositivo_id="SENSOR-001"
                )
                leitura["intermitente"] = True
                leituras.append(leitura)
            timestamp += timedelta(minutes=intervalo_minutos)

        # Evento de substituição do sensor
        eventos.append(self._generate_event(
            timestamp=falha_fim,
            tipo="SENSOR_SUBSTITUIDO",
            descricao="Sensor SENSOR-001 substituído por SENSOR-002"
        ))

        # Período normal com novo sensor
        while timestamp < fim:
            leitura = self._generate_reading(
                timestamp=timestamp,
                temperatura_base=5.0,
                umidade_base=50.0,
                dispositivo_id="SENSOR-002"
            )
            leituras.append(leitura)
            timestamp += timedelta(minutes=intervalo_minutos)

        return {
            "cenario": "falha_sensor",
            "descricao": "Falha ou interrupção de um sensor com lacunas na série de leituras",
            "inicio": inicio.isoformat(),
            "fim": fim.isoformat(),
            "leituras": leituras,
            "eventos": eventos,
            "lacunas": self._contar_lacunas(leituras, intervalo_minutos),
            "estatisticas": self._calcular_estatisticas(leituras),
            "simulado": True
        }

    def gerar_cenario_recuperacao(
        self,
        duracao_horas: int = 8,
        intervalo_minutos: int = 15
    ) -> Dict[str, Any]:
        """
        Gera cenário de recuperação do ambiente após restabelecimento.

        O cenário simula:
        - Período de crise (temperatura elevada)
        - Início das ações de recuperação
        - Retorno gradual às condições ideais

        Args:
            duracao_horas: Duração total do cenário em horas
            intervalo_minutos: Intervalo entre leituras em minutos

        Returns:
            Dicionário com cenário completo
        """
        inicio = datetime.now() - timedelta(hours=duracao_horas)
        crise_inicio = inicio
        crise_fim = inicio + timedelta(hours=3)
        recuperacao_inicio = crise_fim
        fim = inicio + timedelta(hours=duracao_horas)

        leituras = []
        eventos = []
        timestamp = inicio

        # Período de crise - temperatura elevada
        while timestamp < crise_fim:
            variacao_temp = 4.0  # Temperatura elevada
            leitura = self._generate_reading(
                timestamp=timestamp,
                temperatura_base=5.0,
                umidade_base=50.0,
                variacao_temp=variacao_temp
            )
            leituras.append(leitura)
            timestamp += timedelta(minutes=intervalo_minutos)

        # Evento de início da recuperação
        eventos.append(self._generate_event(
            timestamp=recuperacao_inicio,
            tipo="INICIO_RECUPERACAO",
            descricao="Ações de recuperação iniciadas - resfriamento ativo"
        ))

        # Período de recuperação gradual
        tempo_recuperacao = 0
        while timestamp < fim:
            # Temperatura volta ao normal gradualmente
            variacao_temp = max(0, 4.0 - tempo_recuperacao * 0.8)
            leitura = self._generate_reading(
                timestamp=timestamp,
                temperatura_base=5.0,
                umidade_base=50.0,
                variacao_temp=variacao_temp
            )
            leituras.append(leitura)
            timestamp += timedelta(minutes=intervalo_minutos)
            tempo_recuperacao += intervalo_minutos / 60.0

        # Evento de recuperação completa
        eventos.append(self._generate_event(
            timestamp=fim,
            tipo="RECUPERACAO_COMPLETA",
            descricao="Ambiente recuperado - condições ideais restauradas"
        ))

        return {
            "cenario": "recuperacao",
            "descricao": "Recuperação do ambiente após restabelecimento das condições",
            "inicio": inicio.isoformat(),
            "fim": fim.isoformat(),
            "leituras": leituras,
            "eventos": eventos,
            "estatisticas": self._calcular_estatisticas(leituras),
            "simulado": True
        }

    def _calcular_estatisticas(self, leituras: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcula estatísticas das leituras."""
        if not leituras:
            return {}

        temperaturas = [l["temperatura"] for l in leituras]
        umidades = [l["umidade"] for l in leituras]
        status = [l["status"] for l in leituras]

        return {
            "total_leituras": len(leituras),
            "temperatura_min": round(min(temperaturas), 2),
            "temperatura_max": round(max(temperaturas), 2),
            "temperatura_media": round(sum(temperaturas) / len(temperaturas), 2),
            "umidade_min": round(min(umidades), 1),
            "umidade_max": round(max(umidades), 1),
            "umidade_media": round(sum(umidades) / len(umidades), 1),
            "status_normal": status.count("NORMAL"),
            "status_alerta": status.count("ALERTA"),
            "status_critico": status.count("CRÍTICO"),
            "status_frio": status.count("FRIO")
        }

    def _contar_lacunas(self, leituras: List[Dict[str, Any]], intervalo_minutos: int) -> int:
        """Conta lacunas na série de leituras."""
        if len(leituras) < 2:
            return 0

        lacunas = 0
        for i in range(1, len(leituras)):
            tempo_atual = datetime.fromisoformat(leituras[i]["timestamp"])
            tempo_anterior = datetime.fromisoformat(leituras[i-1]["timestamp"])
            diferenca = (tempo_atual - tempo_anterior).total_seconds() / 60
            if diferenca > intervalo_minutos * 1.5:  # Mais de 1.5x o intervalo esperado
                lacunas += 1

        return lacunas

    def obter_cenario(self, tipo: str, **kwargs) -> Dict[str, Any]:
        """
        Obtém um cenário pelo tipo.

        Args:
            tipo: Tipo do cenário (falha_energia, falha_rede, falha_sensor, recuperacao)
            **kwargs: Parâmetros adicionais para o cenário

        Returns:
            Dicionário com cenário

        Raises:
            ValueError: Se tipo não for reconhecido
        """
        cenarios = {
            "falha_energia": self.gerar_cenario_falha_energia,
            "falha_rede": self.gerar_cenario_falha_rede,
            "falha_sensor": self.gerar_cenario_falha_sensor,
            "recuperacao": self.gerar_cenario_recuperacao
        }

        if tipo not in cenarios:
            raise ValueError(f"Cenário não reconhecido: {tipo}. Opções: {list(cenarios.keys())}")

        return cenarios[tipo](**kwargs)

    def listar_cenarios(self) -> List[Dict[str, str]]:
        """Lista os cenários disponíveis."""
        return [
            {
                "id": "falha_energia",
                "nome": "Falha de Energia",
                "descricao": "Falha de energia com aumento gradual de temperatura"
            },
            {
                "id": "falha_rede",
                "nome": "Falha de Rede",
                "descricao": "Indisponibilidade de rede com leituras pendentes"
            },
            {
                "id": "falha_sensor",
                "nome": "Falha de Sensor",
                "descricao": "Falha ou interrupção de um sensor com lacunas na série de leituras"
            },
            {
                "id": "recuperacao",
                "nome": "Recuperação",
                "descricao": "Recuperação do ambiente após restabelecimento das condições"
            }
        ]
