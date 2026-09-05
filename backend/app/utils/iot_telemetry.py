"""
IoT Telemetry - Simulador de Sensores de Armazenamento
Simula leitura de sensores térmicos (ESP32/DHT22) para monitoramento de temperatura e umidade
em ambiente de farmácia/geladeira de conservação de medicamentos
Disciplina: Fundamentos de IoT - Dispositivos Físicos e Geofencing
"""

import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SensorReading:
    """Classe de dados para leitura de sensor IoT"""
    sensor_id: str
    temperatura: float
    umidade: float
    timestamp: datetime
    localizacao: str
    status: str


class IoTTelemetrySimulator:
    """
    Simulador de telemetria IoT para sensores de armazenamento.
    Simula sensores DHT22/ESP32 em ambientes de conservação.
    """
    
    # Configurações dos sensores simulados
    SENSORES = {
        'geladeira_principal': {
            'id': 'ESP32-001',
            'localizacao': 'Geladeira Principal - Medicamentos Controlados',
            'temp_min': 2.0,
            'temp_max': 8.0,
            'umidade_min': 30,
            'umidade_max': 60
        },
        'geladeira_secundaria': {
            'id': 'ESP32-002',
            'localizacao': 'Geladeira Secundária - Antibióticos',
            'temp_min': 2.0,
            'temp_max': 8.0,
            'umidade_min': 30,
            'umidade_max': 60
        },
        'almoxarifado': {
            'id': 'ESP32-003',
            'localizacao': 'Almoxarifado - Medicamentos de Uso Contínuo',
            'temp_min': 18.0,
            'temp_max': 25.0,
            'umidade_min': 40,
            'umidade_max': 70
        }
    }
    
    # Histórico de leituras (últimas 100 leituras por sensor)
    _historico: Dict[str, List[SensorReading]] = {}
    
    def __init__(self):
        """Inicializa o simulador de telemetria"""
        for sensor_key in self.SENSORES:
            self._historico[sensor_key] = []
    
    def simular_leitura(self, sensor_key: str) -> SensorReading:
        """
        Simula uma leitura de sensor com variação realista.
        
        Args:
            sensor_key: Chave do sensor (ex: 'geladeira_principal')
        
        Returns:
            SensorReading com os dados simulados
        """
        if sensor_key not in self.SENSORES:
            raise ValueError(f"Sensor {sensor_key} não configurado")
        
        config = self.SENSORES[sensor_key]
        
        # Simula variação baseada na leitura anterior ou valor médio
        historico_sensor = self._historico[sensor_key]
        
        if historico_sensor:
            ultima_leitura = historico_sensor[-1]
            # Variação pequena em relação à leitura anterior (±0.5°C, ±5% umidade)
            temp_base = ultima_leitura.temperatura
            umidade_base = ultima_leitura.umidade
        else:
            # Valor médio da faixa
            temp_base = (config['temp_min'] + config['temp_max']) / 2
            umidade_base = (config['umidade_min'] + config['umidade_max']) / 2
        
        # Adiciona variação aleatória
        temperatura = round(temp_base + random.uniform(-0.5, 0.5), 2)
        umidade = round(umidade_base + random.uniform(-5, 5), 1)
        
        # Garante que está dentro da faixa
        temperatura = max(config['temp_min'], min(config['temp_max'], temperatura))
        umidade = max(config['umidade_min'], min(config['umidade_max'], umidade))
        
        # Determina status
        status = self._determinar_status(sensor_key, temperatura, umidade)
        
        leitura = SensorReading(
            sensor_id=config['id'],
            temperatura=temperatura,
            umidade=umidade,
            timestamp=datetime.utcnow(),
            localizacao=config['localizacao'],
            status=status
        )
        
        # Adiciona ao histórico
        self._historico[sensor_key].append(leitura)
        
        # Mantém apenas as últimas 100 leituras
        if len(self._historico[sensor_key]) > 100:
            self._historico[sensor_key].pop(0)
        
        return leitura
    
    def _determinar_status(self, sensor_key: str, temperatura: float, umidade: float) -> str:
        """
        Determina o status baseado nos limites configurados.
        """
        config = self.SENSORES[sensor_key]
        
        # Verifica temperatura crítica (> 25°C para qualquer sensor)
        if temperatura > 25.0:
            return 'CRÍTICO - Temperatura Alta'
        
        # Verifica fora da faixa
        if temperatura < config['temp_min'] or temperatura > config['temp_max']:
            return 'ALERTA - Temperatura Fora da Faixa'
        
        if umidade < config['umidade_min'] or umidade > config['umidade_max']:
            return 'ALERTA - Umidade Fora da Faixa'
        
        # Verifica próximo do limite
        margem = 1.0  # 1°C de margem
        if temperatura >= config['temp_max'] - margem or temperatura <= config['temp_min'] + margem:
            return 'ATENÇÃO - Próximo do Limite'
        
        return 'NORMAL'
    
    def adicionar_leitura_manual(self, farmacia_id: str, temperatura: float, umidade: float, status: str):
        """
        Adiciona uma leitura manual de temperatura e umidade.
        
        Args:
            farmacia_id: ID da farmácia vinculada
            temperatura: Temperatura em graus Celsius
            umidade: Umidade em porcentagem
            status: Status do refrigerador (NORMAL, ALERTA, CRÍTICO)
        """
        # Cria uma leitura manual com base na farmácia
        sensor_key = f"manual_{farmacia_id}"
        
        if sensor_key not in self._historico:
            self._historico[sensor_key] = []
        
        leitura = SensorReading(
            sensor_id=f"MANUAL-{farmacia_id}",
            temperatura=temperatura,
            umidade=umidade,
            timestamp=datetime.utcnow(),
            localizacao=f"Farmácia ID {farmacia_id} - Registro Manual",
            status=status
        )
        
        self._historico[sensor_key].append(leitura)
        
        # Mantém apenas as últimas 100 leituras
        if len(self._historico[sensor_key]) > 100:
            self._historico[sensor_key].pop(0)
        
        logger.info(f"Leitura manual adicionada: Farmácia {farmacia_id}, {temperatura}°C, {umidade}% umidade, status {status}")
    
    def obter_leitura_atual(self, sensor_key: str) -> Optional[Dict]:
        """
        Obtém a leitura mais recente de um sensor.
        
        Args:
            sensor_key: Chave do sensor
        
        Returns:
            Dict com os dados da leitura ou None se não houver leituras
        """
        historico_sensor = self._historico.get(sensor_key, [])
        
        if not historico_sensor:
            # Gera uma leitura se não houver histórico
            leitura = self.simular_leitura(sensor_key)
        else:
            leitura = historico_sensor[-1]
        
        return {
            'sensor_id': leitura.sensor_id,
            'sensor_key': sensor_key,
            'localizacao': leitura.localizacao,
            'temperatura': leitura.temperatura,
            'umidade': leitura.umidade,
            'timestamp': leitura.timestamp.isoformat(),
            'status': leitura.status
        }
    
    def obter_todas_leituras(self) -> List[Dict]:
        """
        Obtém leituras de todos os sensores configurados.
        
        Returns:
            Lista de dicts com as leituras atuais
        """
        leituras = []
        
        for sensor_key in self.SENSORES:
            leitura = self.obter_leitura_atual(sensor_key)
            if leitura:
                leituras.append(leitura)
        
        return leituras
    
    def obter_historico(self, sensor_key: str, limite: int = 24) -> List[Dict]:
        """
        Obtém o histórico de leituras de um sensor.
        
        Args:
            sensor_key: Chave do sensor
            limite: Número máximo de leituras a retornar
        
        Returns:
            Lista de dicts com o histórico
        """
        historico_sensor = self._historico.get(sensor_key, [])
        
        return [
            {
                'sensor_id': leitura.sensor_id,
                'temperatura': leitura.temperatura,
                'umidade': leitura.umidade,
                'timestamp': leitura.timestamp.isoformat(),
                'status': leitura.status
            }
            for leitura in historico_sensor[-limite:]
        ]
    
    def verificar_alertas_criticos(self) -> List[Dict]:
        """
        Verifica se há alertas críticos em qualquer sensor.
        
        Returns:
            Lista de sensores com alertas críticos
        """
        alertas = []
        
        for sensor_key in self.SENSORES:
            leitura = self.obter_leitura_atual(sensor_key)
            if leitura and 'CRÍTICO' in leitura['status']:
                alertas.append(leitura)
        
        return alertas


# Instância global do simulador
iot_simulator = IoTTelemetrySimulator()


def processar_leitura_iot(sensor_key: str, temperatura: float, umidade: float) -> Dict:
    """
    Processa uma leitura recebida de um sensor IoT real.
    
    Args:
        sensor_key: Chave do sensor
        temperatura: Temperatura em °C
        umidade: Umidade relativa em %
    
    Returns:
        Dict com a leitura processada e status
    """
    if sensor_key not in iot_simulator.SENSORES:
        return {
            'erro': f'Sensor {sensor_key} não configurado',
            'status': 'erro'
        }
    
    config = iot_simulator.SENSORES[sensor_key]
    
    # Determina status
    status = iot_simulator._determinar_status(sensor_key, temperatura, umidade)
    
    leitura = SensorReading(
        sensor_id=config['id'],
        temperatura=temperatura,
        umidade=umidade,
        timestamp=datetime.utcnow(),
        localizacao=config['localizacao'],
        status=status
    )
    
    # Adiciona ao histórico
    iot_simulator._historico[sensor_key].append(leitura)
    
    # Mantém apenas as últimas 100 leituras
    if len(iot_simulator._historico[sensor_key]) > 100:
        iot_simulator._historico[sensor_key].pop(0)
    
    # Registra alerta se crítico
    if 'CRÍTICO' in status:
        logger.warning(
            f"ALERTA CRÍTICO IoT - Sensor {config['id']}: "
            f"Temperatura {temperatura}°C, Umidade {umidade}% em {config['localizacao']}"
        )
    
    return {
        'sensor_id': leitura.sensor_id,
        'sensor_key': sensor_key,
        'localizacao': leitura.localizacao,
        'temperatura': leitura.temperatura,
        'umidade': leitura.umidade,
        'timestamp': leitura.timestamp.isoformat(),
        'status': leitura.status,
        'alerta_critico': 'CRÍTICO' in status
    }


# ============================================================================
# RFID/NFC SIMULATION - Trava Digital para Armário de Medicamentos Controlados
# ============================================================================

@dataclass
class RFIDTag:
    """Representa uma tag RFID/NFC de um farmacêutico"""
    tag_id: str
    usuario_id: int
    nome: str
    cargo: str
    ativa: bool = True


class RFIDAuthenticator:
    """
    Simulador de autenticação RFID/NFC para armário de medicamentos controlados.
    Simula leitura de crachá/tag do farmacêutico responsável.
    """
    
    def __init__(self):
        """Inicializa o autenticador RFID"""
        self.tags_registradas: Dict[str, RFIDTag] = {}
        self._carregar_tags()
        self._log_acessos: List[Dict] = []
    
    def _carregar_tags(self):
        """
        Carrega tags RFID registradas.
        Em produção, isso viria do banco de dados.
        """
        # Tags de exemplo (em produção, carregar do banco)
        self.tags_registradas = {
            'RFID-001-FARM': RFIDTag(
                tag_id='RFID-001-FARM',
                usuario_id=1,
                nome='Dr. João Silva',
                cargo='Farmacêutico',
                ativa=True
            ),
            'RFID-002-FARM': RFIDTag(
                tag_id='RFID-002-FARM',
                usuario_id=2,
                nome='Dra. Maria Santos',
                cargo='Farmacêutico',
                ativa=True
            ),
            'RFID-003-ADM': RFIDTag(
                tag_id='RFID-003-ADM',
                usuario_id=3,
                nome='Admin Sistema',
                cargo='Administrador',
                ativa=True
            )
        }
    
    def validar_tag(self, tag_id: str) -> Optional[RFIDTag]:
        """
        Valida uma tag RFID/NFC.
        
        Args:
            tag_id: ID da tag a validar
        
        Returns:
            RFIDTag se válida, None caso contrário
        """
        tag = self.tags_registradas.get(tag_id)
        
        if not tag:
            logger.warning(f"Tag RFID não reconhecida: {tag_id}")
            return None
        
        if not tag.ativa:
            logger.warning(f"Tag RFID desativada: {tag_id}")
            return None
        
        return tag
    
    def registrar_acesso(self, tag_id: str, gaveta_id: str, acao: str):
        """
        Registra um acesso ao armário no log de auditoria.
        
        Args:
            tag_id: ID da tag RFID
            gaveta_id: ID da gaveta acessada
            acao: Ação realizada ('abrir', 'fechar')
        """
        tag = self.validar_tag(tag_id)
        
        if not tag:
            return False
        
        log = {
            'timestamp': datetime.utcnow().isoformat(),
            'tag_id': tag_id,
            'usuario_id': tag.usuario_id,
            'usuario_nome': tag.nome,
            'cargo': tag.cargo,
            'gaveta_id': gaveta_id,
            'acao': acao
        }
        
        self._log_acessos.append(log)
        logger.info(f"RFID Acesso registrado: {tag.nome} - {acao} gaveta {gaveta_id}")
        
        return True
    
    def obter_historico_acessos(self, limite: int = 50) -> List[Dict]:
        """
        Obtém o histórico de acessos RFID.
        
        Args:
            limite: Número máximo de registros
        
        Returns:
            Lista de acessos
        """
        return self._log_acessos[-limite:]


# Instância global do autenticador RFID
_rfid_authenticator: Optional[RFIDAuthenticator] = None


def obter_rfid_authenticator() -> RFIDAuthenticator:
    """
    Obtém a instância global do autenticador RFID.
    """
    global _rfid_authenticator
    if _rfid_authenticator is None:
        _rfid_authenticator = RFIDAuthenticator()
    return _rfid_authenticator


def autenticar_rfid(tag_id: str, gaveta_id: str = 'CONTROLADOS') -> Dict:
    """
    Autentica uma tag RFID e registra abertura de gaveta.
    
    Args:
        tag_id: ID da tag RFID
        gaveta_id: ID da gaveta (padrão: 'CONTROLADOS')
    
    Returns:
        Dict com resultado da autenticação
    """
    authenticator = obter_rfid_authenticator()
    tag = authenticator.validar_tag(tag_id)
    
    if not tag:
        return {
            'sucesso': False,
            'mensagem': 'Tag RFID não reconhecida ou desativada',
            'autorizado': False
        }
    
    # Registra o acesso
    authenticator.registrar_acesso(tag_id, gaveta_id, 'abrir')
    
    return {
        'sucesso': True,
        'mensagem': 'Autenticação RFID realizada com sucesso',
        'autorizado': True,
        'usuario': {
            'id': tag.usuario_id,
            'nome': tag.nome,
            'cargo': tag.cargo
        },
        'gaveta': gaveta_id,
        'timestamp': datetime.utcnow().isoformat()
    }
