"""
Serviço de Radar de Integridade da Telemetria.

Analisa telemetria IoT persistida e aponta padrões que merecem conferência.

LIMITAÇÕES:
- LeituraIoT não guarda horário de recebimento separado por leitura (apenas em LoteTelemetria)
- Endpoint de lote não recebe ID de evento ou número sequencial confiável
- dispositivo_id vem do payload e não é prova de autenticidade
- Não é possível comprovar atraso de transmissão, perda de leituras, duplicação real ou ordem original

CAPACIDADES NÃO VERIFICÁVEIS:
- Atraso entre envio e recebimento (sem horário de recebimento por leitura)
- Perda de leituras (sem sequência confiável)
- Duplicação real (sem ID único por leitura)
- Ordem original do dispositivo (sem sequência)
- Autenticação do dispositivo (ID do payload não é prova)
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from sqlalchemy import func, and_
from app.database import db
from app.models.iot import LeituraIoT


class IotIntegrityRadarService:
    """Serviço de Radar de Integridade da Telemetria."""

    # Limites de parâmetros
    MAX_PERIODO_DIAS = 90  # Máximo de 90 dias de período
    MIN_PERIODO_DIAS = 1
    MAX_PAGINA = 100
    TOLERANCIA_FUTURO_MINUTOS = 60  # Tolerância para timestamps no futuro (60 minutos)

    # Intervalos de análise disponíveis (hipóteses)
    INTERVALOS_ANALISE = {
        '5min': 5,
        '15min': 15,
        '30min': 30,
        '1h': 60,
        '6h': 360,
        '12h': 720,
        '24h': 1440
    }

    def __init__(self):
        """Inicializa o serviço."""
        pass

    def analisar_frescor(self, periodo_dias: int = 7) -> List[Dict[str, Any]]:
        """
        Analisa frescor da telemetria por dispositivo.

        Args:
            periodo_dias: Período em dias para análise (1-90)

        Returns:
            Lista de dispositivos com última leitura e frescor
        """
        if periodo_dias < self.MIN_PERIODO_DIAS or periodo_dias > self.MAX_PERIODO_DIAS:
            raise ValueError(f"Período deve ser entre {self.MIN_PERIODO_DIAS} e {self.MAX_PERIODO_DIAS} dias")

        data_limite = datetime.utcnow() - timedelta(days=periodo_dias)

        # Buscar última leitura por dispositivo
        ultimas_leituras = db.session.query(
            LeituraIoT.dispositivo_id,
            func.max(LeituraIoT.data_hora).label('ultima_leitura'),
            func.count(LeituraIoT.id).label('total_leituras')
        ).filter(
            LeituraIoT.data_hora >= data_limite
        ).group_by(
            LeituraIoT.dispositivo_id
        ).all()

        dispositivos = []
        agora = datetime.utcnow()

        for dispositivo_id, ultima_leitura, total_leituras in ultimas_leituras:
            if ultima_leitura:
                horas_desde_ultima = (agora - ultima_leitura).total_seconds() / 3600
                dias_desde_ultima = horas_desde_ultima / 24

                if dias_desde_ultima < 1:
                    status_frescor = "recente"
                elif dias_desde_ultima < 7:
                    status_frescor = "moderado"
                else:
                    status_frescor = "antigo"
            else:
                horas_desde_ultima = None
                dias_desde_ultima = None
                status_frescor = "sem_dados"

            dispositivos.append({
                'dispositivo_id': dispositivo_id,
                'ultima_leitura': ultima_leitura.isoformat() if ultima_leitura else None,
                'horas_desde_ultima': horas_desde_ultima,
                'dias_desde_ultima': dias_desde_ultima,
                'status_frescor': status_frescor,
                'total_leituras': total_leituras
            })

        # Ordenar por frescor (mais antigos primeiro)
        dispositivos.sort(key=lambda x: x['dias_desde_ultima'] or 999, reverse=True)

        return dispositivos

    def analisar_lacunas_temporais(
        self,
        intervalo_minutos: str = '1h',
        farmacia_id: Optional[int] = None,
        dispositivo_id: Optional[str] = None,
        periodo_dias: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Analisa lacunas temporais na telemetria.

        Args:
            intervalo_minutos: Intervalo esperado entre leituras (chave de INTERVALOS_ANALISE)
            farmacia_id: Filtro opcional por farmácia
            dispositivo_id: Filtro opcional por dispositivo
            periodo_dias: Período em dias para análise (1-90)

        Returns:
            Lista de lacunas temporais detectadas
        """
        if intervalo_minutos not in self.INTERVALOS_ANALISE:
            raise ValueError(f"Intervalo deve ser um de: {list(self.INTERVALOS_ANALISE.keys())}")

        if periodo_dias < self.MIN_PERIODO_DIAS or periodo_dias > self.MAX_PERIODO_DIAS:
            raise ValueError(f"Período deve ser entre {self.MIN_PERIODO_DIAS} e {self.MAX_PERIODO_DIAS} dias")

        intervalo_esperado = self.INTERVALOS_ANALISE[intervalo_minutos]
        data_inicio = datetime.utcnow() - timedelta(days=periodo_dias)

        # Construir query
        query = LeituraIoT.query.filter(
            LeituraIoT.data_hora >= data_inicio
        )

        if farmacia_id:
            query = query.filter(LeituraIoT.farmacia_id == farmacia_id)

        if dispositivo_id:
            query = query.filter(LeituraIoT.dispositivo_id == dispositivo_id)

        # Ordenar por dispositivo e timestamp
        leituras = query.order_by(
            LeituraIoT.dispositivo_id,
            LeituraIoT.data_hora
        ).all()

        # Analisar lacunas por dispositivo
        lacunas = []
        leituras_por_dispositivo = {}

        for leitura in leituras:
            dispositivo = leitura.dispositivo_id
            if dispositivo not in leituras_por_dispositivo:
                leituras_por_dispositivo[dispositivo] = []
            leituras_por_dispositivo[dispositivo].append(leitura)

        for dispositivo, lista_leituras in leituras_por_dispositivo.items():
            if len(lista_leituras) < 2:
                continue  # Não há lacunas detectáveis com menos de 2 leituras

            for i in range(1, len(lista_leituras)):
                leitura_anterior = lista_leituras[i - 1]
                leitura_atual = lista_leituras[i]

                delta_minutos = (leitura_atual.data_hora - leitura_anterior.data_hora).total_seconds() / 60

                # Se o intervalo for maior que o esperado (com tolerância de 50%)
                if delta_minutos > intervalo_esperado * 1.5:
                    lacunas.append({
                        'dispositivo_id': dispositivo,
                        'farmacia_id': leitura_atual.farmacia_id,
                        'timestamp_anterior': leitura_anterior.data_hora.isoformat(),
                        'timestamp_atual': leitura_atual.data_hora.isoformat(),
                        'delta_minutos': delta_minutos,
                        'intervalo_esperado_minutos': intervalo_esperado,
                        'gravidade': 'alta' if delta_minutos > intervalo_esperado * 3 else 'moderada'
                    })

        return lacunas

    def analisar_duplicidade_candidatos(
        self,
        periodo_dias: int = 7,
        farmacia_id: Optional[int] = None,
        dispositivo_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Analisa candidatos a duplicidade (leituras idênticas).

        Agrupa somente leituras com igualdade exata em dispositivo, farmácia,
        timestamp e valores medidos.

        Args:
            periodo_dias: Período em dias para análise (1-90)
            farmacia_id: Filtro opcional por farmácia
            dispositivo_id: Filtro opcional por dispositivo

        Returns:
            Lista de grupos de leituras idênticas
        """
        if periodo_dias < self.MIN_PERIODO_DIAS or periodo_dias > self.MAX_PERIODO_DIAS:
            raise ValueError(f"Período deve ser entre {self.MIN_PERIODO_DIAS} e {self.MAX_PERIODO_DIAS} dias")

        data_inicio = datetime.utcnow() - timedelta(days=periodo_dias)

        # Construir query
        query = LeituraIoT.query.filter(
            LeituraIoT.data_hora >= data_inicio
        )

        if farmacia_id:
            query = query.filter(LeituraIoT.farmacia_id == farmacia_id)

        if dispositivo_id:
            query = query.filter(LeituraIoT.dispositivo_id == dispositivo_id)

        leituras = query.all()

        # Agrupar por fingerprint (dispositivo + farmácia + timestamp + valores)
        grupos = {}
        for leitura in leituras:
            fingerprint = (
                leitura.dispositivo_id,
                leitura.farmacia_id,
                leitura.data_hora.isoformat(),
                leitura.temperatura,
                leitura.umidade,
                leitura.luminosidade_lux
            )

            if fingerprint not in grupos:
                grupos[fingerprint] = []
            grupos[fingerprint].append(leitura)

        # Filtrar grupos com mais de 1 leitura (candidatos a duplicidade)
        duplicidades = []
        for fingerprint, grupo in grupos.items():
            if len(grupo) > 1:
                duplicidades.append({
                    'dispositivo_id': grupo[0].dispositivo_id,
                    'farmacia_id': grupo[0].farmacia_id,
                    'timestamp': grupo[0].data_hora.isoformat(),
                    'temperatura': grupo[0].temperatura,
                    'umidade': grupo[0].umidade,
                    'luminosidade_lux': grupo[0].luminosidade_lux,
                    'quantidade': len(grupo),
                    'ids': [l.id for l in grupo]
                })

        # Ordenar por quantidade (mais candidatos primeiro)
        duplicidades.sort(key=lambda x: x['quantidade'], reverse=True)

        return duplicidades

    def analisar_timestamps_futuros(
        self,
        tolerancia_minutos: int = 60,
        periodo_dias: int = 7,
        farmacia_id: Optional[int] = None,
        dispositivo_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Analisa leituras com timestamps no futuro.

        Args:
            tolerancia_minutos: Tolerância em minutos para considerar como futuro
            periodo_dias: Período em dias para análise (1-90)
            farmacia_id: Filtro opcional por farmácia
            dispositivo_id: Filtro opcional por dispositivo

        Returns:
            Lista de leituras com timestamps no futuro
        """
        if periodo_dias < self.MIN_PERIODO_DIAS or periodo_dias > self.MAX_PERIODO_DIAS:
            raise ValueError(f"Período deve ser entre {self.MIN_PERIODO_DIAS} e {self.MAX_PERIODO_DIAS} dias")

        agora = datetime.utcnow()
        limite_futuro = agora + timedelta(minutes=tolerancia_minutos)
        data_inicio = agora - timedelta(days=periodo_dias)

        # Construir query
        query = LeituraIoT.query.filter(
            and_(
                LeituraIoT.data_hora > agora,
                LeituraIoT.data_hora <= limite_futuro,
                LeituraIoT.data_hora >= data_inicio
            )
        )

        if farmacia_id:
            query = query.filter(LeituraIoT.farmacia_id == farmacia_id)

        if dispositivo_id:
            query = query.filter(LeituraIoT.dispositivo_id == dispositivo_id)

        leituras_futuro = query.all()

        futuros = []
        for leitura in leituras_futuro:
            delta_minutos = (leitura.data_hora - agora).total_seconds() / 60
            futuros.append({
                'id': leitura.id,
                'dispositivo_id': leitura.dispositivo_id,
                'farmacia_id': leitura.farmacia_id,
                'data_hora': leitura.data_hora.isoformat(),
                'temperatura': leitura.temperatura,
                'umidade': leitura.umidade,
                'delta_minutos': delta_minutos,
                'tolerancia_minutos': tolerancia_minutos
            })

        # Ordenar por delta (mais no futuro primeiro)
        futuros.sort(key=lambda x: x['delta_minutos'], reverse=True)

        return futuros

    def obter_resumo(
        self,
        periodo_dias: int = 7
    ) -> Dict[str, Any]:
        """
        Obtém resumo dos sinais de integridade.

        Args:
            periodo_dias: Período em dias para análise (1-90)

        Returns:
            Dicionário com resumo dos sinais
        """
        try:
            frescor = self.analisar_frescor(periodo_dias=periodo_dias)
            dispositivos_sem_dados = [d for d in frescor if d['status_frescor'] == 'sem_dados']
            dispositivos_antigos = [d for d in frescor if d['status_frescor'] == 'antigo']
        except Exception:
            frescor = []
            dispositivos_sem_dados = []
            dispositivos_antigos = []

        try:
            lacunas = self.analisar_lacunas_temporais(periodo_dias=periodo_dias)
        except Exception:
            lacunas = []

        try:
            duplicidades = self.analisar_duplicidade_candidatos(periodo_dias=periodo_dias)
        except Exception:
            duplicidades = []

        try:
            futuros = self.analisar_timestamps_futuros(periodo_dias=periodo_dias)
        except Exception:
            futuros = []

        return {
            'periodo_dias': periodo_dias,
            'total_dispositivos': len(frescor),
            'dispositivos_sem_dados': len(dispositivos_sem_dados),
            'dispositivos_antigos': len(dispositivos_antigos),
            'total_lacunas': len(lacunas),
            'total_duplicidades': len(duplicidades),
            'total_futuros': len(futuros),
            'intervalos_disponiveis': list(self.INTERVALOS_ANALISE.keys())
        }
