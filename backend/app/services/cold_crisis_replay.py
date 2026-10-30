"""
Serviço de Replay e Avaliação de Resposta a Crises.

Este serviço estende o Laboratório de Crises com funcionalidades de:
- Replay determinístico de cenários
- Comparação entre execuções
- Avaliação de cobertura de roteiro de treinamento

NOTA: Reutiliza ColdCrisisSimulator. Não cria dados reais.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from app.services.cold_crisis_simulator import ColdCrisisSimulator


class ColdCrisisReplayService:
    """Serviço de replay e avaliação de resposta a crises."""

    # Limites de replay
    MAX_VELOCIDADE = 10  # Multiplicador máximo de velocidade
    MIN_VELOCIDADE = 1   # Multiplicador mínimo de velocidade
    MAX_ETAPAS = 50      # Máximo de etapas por execução
    MAX_COMPARACOES = 2 # Máximo de execuções por comparação

    # Roteiro de treinamento (versão 1.0)
    ROTEIRO_VERSAO = "1.0"
    ROTEIRO_DATA = "2024-01"

    # Etapas do roteiro de treinamento (apenas demonstrativo, não protocolo oficial)
    ROTEIRO_ETAPAS = {
        "falha_energia": [
            {
                "id": "reconhecer_alerta",
                "nome": "Reconhecer o alerta simulado",
                "descricao": "Identificar que o sistema reportou falha de energia"
            },
            {
                "id": "verificar_cobertura",
                "nome": "Verificar cobertura de telemetria",
                "descricao": "Consultar o intervalo de leituras disponíveis no período"
            },
            {
                "id": "avaliar_temperatura",
                "nome": "Avaliar aumento de temperatura",
                "descricao": "Analisar a variação de temperatura durante a falha"
            },
            {
                "id": "consultar_checklist",
                "nome": "Consultar checklist de treinamento",
                "descricao": "Acessar o checklist de procedimentos para falha de energia"
            },
            {
                "id": "encaminhar_responsavel",
                "nome": "Encaminhar para revisão do responsável",
                "descricao": "Documentar o cenário fictício para revisão do responsável"
            }
        ],
        "falha_rede": [
            {
                "id": "reconhecer_falha_rede",
                "nome": "Reconhecer a falha de rede",
                "descricao": "Identificar que há leituras pendentes de transmissão"
            },
            {
                "id": "quantificar_pendentes",
                "nome": "Quantificar leituras pendentes",
                "descricao": "Contar quantas leituras estão acumuladas localmente"
            },
            {
                "id": "verificar_integridade",
                "nome": "Verificar integridade dos dados",
                "descricao": "Confirmar que as leituras pendentes foram enviadas"
            },
            {
                "id": "consultar_checklist",
                "nome": "Consultar checklist de treinamento",
                "descricao": "Acessar o checklist de procedimentos para falha de rede"
            }
        ],
        "falha_sensor": [
            {
                "id": "identificar_sensor",
                "nome": "Identificar sensor com falha",
                "descricao": "Localizar qual sensor está reportando lacunas"
            },
            {
                "id": "avaliar_lacunas",
                "nome": "Avaliar lacunas na série",
                "descricao": "Analisar o intervalo de dados ausentes"
            },
            {
                "id": "verificar_substituicao",
                "nome": "Verificar substituição de sensor",
                "descricao": "Confirmar que o sensor foi substituído corretamente"
            },
            {
                "id": "consultar_checklist",
                "nome": "Consultar checklist de treinamento",
                "descricao": "Acessar o checklist de procedimentos para falha de sensor"
            }
        ],
        "recuperacao": [
            {
                "id": "monitorar_recuperacao",
                "nome": "Monitorar recuperação gradual",
                "descricao": "Acompanhar o retorno às condições ideais"
            },
            {
                "id": "validar_condicoes",
                "nome": "Validar condições finais",
                "descricao": "Confirmar que o ambiente está dentro dos parâmetros ideais"
            },
            {
                "id": "documentar_tempo",
                "nome": "Documentar tempo de recuperação",
                "descricao": "Registrar o tempo necessário para estabilização"
            },
            {
                "id": "consultar_checklist",
                "nome": "Consultar checklist de treinamento",
                "descricao": "Acessar o checklist de procedimentos para recuperação"
            }
        ]
    }

    def __init__(self):
        """Inicializa o serviço de replay."""
        self.simulator = ColdCrisisSimulator()

    def obter_roteiro(self, cenario: str) -> List[Dict[str, str]]:
        """
        Obtém o roteiro de treinamento para um cenário.

        Args:
            cenario: Tipo do cenário

        Returns:
            Lista de etapas do roteiro
        """
        if cenario not in self.ROTEIRO_ETAPAS:
            return []

        return self.ROTEIRO_ETAPAS[cenario]

    def obter_informacao_roteiro(self) -> Dict[str, str]:
        """
        Obtém informações sobre o roteiro de treinamento.

        Returns:
            Dicionário com versão e data do roteiro
        """
        return {
            "versao": self.ROTEIRO_VERSAO,
            "data": self.ROTEIRO_DATA,
            "aviso": "Este roteiro é material demonstrativo de treinamento. Não representa procedimento oficial, protocolo clínico, orientação da Anvisa ou política operacional aprovada."
        }

    def iniciar_replay(
        self,
        cenario: str,
        duracao_horas: int,
        intervalo_minutos: int,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Inicia um replay de um cenário.

        Args:
            cenario: Tipo do cenário
            duracao_horas: Duração em horas
            intervalo_minutos: Intervalo em minutos
            seed: Seed para reprodutibilidade

        Returns:
            Dicionário com execução de replay
        """
        # Usar seed específica para replay
        if seed is None:
            seed = int(datetime.now().timestamp())

        # Gerar cenário com seed
        simulador = ColdCrisisSimulator(seed=seed)
        resultado = simulador.obter_cenario(
            tipo=cenario,
            duracao_horas=duracao_horas,
            intervalo_minutos=intervalo_minutos
        )

        # Preparar execução de replay
        execucao = {
            "id": f"replay_{seed}",
            "cenario": cenario,
            "seed": seed,
            "inicio": datetime.utcnow().isoformat(),
            "duracao_horas": duracao_horas,
            "intervalo_minutos": intervalo_minutos,
            "etapas_cobertas": [],
            "etapas_pendentes": self.obter_roteiro(cenario),
            "tempo_virtual": 0,
            "escolhas": [],
            "resultado_cenario": resultado,
            "concluido": False
        }

        return execucao

    def adicionar_escolha(
        self,
        execucao: Dict[str, Any],
        etapa_id: str,
        tempo_virtual: float
    ) -> Dict[str, Any]:
        """
        Adiciona uma escolha do participante à execução.

        Args:
            execucao: Execução atual
            etapa_id: ID da etapa escolhida
            tempo_virtual: Tempo virtual decorrido

        Returns:
            Execução atualizada
        """
        # Verificar se a etapa está no roteiro
        etapas_pendentes = [e for e in execucao["etapas_pendentes"] if e["id"] == etapa_id]
        if not etapas_pendentes:
            return execucao

        # Adicionar escolha
        escolha = {
            "etapa_id": etapa_id,
            "tempo_virtual": tempo_virtual,
            "timestamp": datetime.utcnow().isoformat()
        }
        execucao["escolhas"].append(escolha)

        # Marcar etapa como coberta
        execucao["etapas_cobertas"].append(etapas_pendentes[0])
        execucao["etapas_pendentes"] = [
            e for e in execucao["etapas_pendentes"] if e["id"] != etapa_id
        ]

        # Atualizar tempo virtual
        execucao["tempo_virtual"] = tempo_virtual

        # Verificar se concluído
        if not execucao["etapas_pendentes"]:
            execucao["concluido"] = True
            execucao["fim"] = datetime.utcnow().isoformat()

        return execucao

    def calcular_cobertura(self, execucao: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calcula a cobertura do roteiro de treinamento.

        Args:
            execucao: Execução do replay

        Returns:
            Dicionário com métricas de cobertura
        """
        total_etapas = len(execucao["etapas_cobertas"]) + len(execucao["etapas_pendentes"])
        etapas_cobertas = len(execucao["etapas_cobertas"])

        if total_etapas == 0:
            porcentagem = 0
        else:
            porcentagem = (etapas_cobertas / total_etapas) * 100

        return {
            "total_etapas": total_etapas,
            "etapas_cobertas": etapas_cobertas,
            "etapas_pendentes": len(execucao["etapas_pendentes"]),
            "porcentagem_cobertura": round(porcentagem, 1),
            "concluido": execucao["concluido"]
        }

    def comparar_execucoes(
        self,
        execucao1: Dict[str, Any],
        execucao2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compara duas execuções do mesmo cenário.

        Args:
            execucao1: Primeira execução
            execucao2: Segunda execução

        Returns:
            Dicionário com comparação
        """
        # Verificar se são do mesmo cenário
        if execucao1["cenario"] != execucao2["cenario"]:
            raise ValueError("As execuções devem ser do mesmo cenário")

        # Calcular cobertura de cada execução
        cobertura1 = self.calcular_cobertura(execucao1)
        cobertura2 = self.calcular_cobertura(execucao2)

        # Comparar etapas cobertas
        etapas_comuns = set(e["id"] for e in execucao1["etapas_cobertas"]) & set(e["id"] for e in execucao2["etapas_cobertas"])
        etapas_exclusivas_1 = set(e["id"] for e in execucao1["etapas_cobertas"]) - etapas_comuns
        etapas_exclusivas_2 = set(e["id"] for e in execucao2["etapas_cobertas"]) - etapas_comuns

        return {
            "cenario": execucao1["cenario"],
            "cobertura1": cobertura1,
            "cobertura2": cobertura2,
            "etapas_comuns": list(etapas_comuns),
            "etapas_exclusivas_1": list(etapas_exclusivas_1),
            "etapas_exclusivas_2": list(etapas_exclusivas_2),
            "tempo_virtual_1": execucao1["tempo_virtual"],
            "tempo_virtual_2": execucao2["tempo_virtual"],
            "diferenca_tempo": execucao2["tempo_virtual"] - execucao1["tempo_virtual"]
        }

    def validar_parametros_replay(
        self,
        cenario: str,
        duracao_horas: int,
        intervalo_minutos: int,
        velocidade: int = 1
    ) -> None:
        """
        Valida parâmetros de replay.

        Args:
            cenario: Tipo do cenário
            duracao_horas: Duração em horas
            intervalo_minutos: Intervalo em minutos
            velocidade: Multiplicador de velocidade

        Raises:
            ValueError: Se parâmetros forem inválidos
        """
        # Validar cenário
        cenarios_validos = ["falha_energia", "falha_rede", "falha_sensor", "recuperacao"]
        if cenario not in cenarios_validos:
            raise ValueError(f"Cenário inválido. Opções: {cenarios_validos}")

        # Validar duração
        if duracao_horas < 1 or duracao_horas > 24:
            raise ValueError("Duração deve ser entre 1 e 24 horas")

        # Validar intervalo
        if intervalo_minutos < 1 or intervalo_minutos > 60:
            raise ValueError("Intervalo deve ser entre 1 e 60 minutos")

        # Validar velocidade
        if velocidade < self.MIN_VELOCIDADE or velocidade > self.MAX_VELOCIDADE:
            raise ValueError(f"Velocidade deve ser entre {self.MIN_VELOCIDADE} e {self.MAX_VELOCIDADE}")
