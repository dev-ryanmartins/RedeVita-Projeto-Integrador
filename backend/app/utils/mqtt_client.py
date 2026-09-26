"""
MQTT Client Handler - Cliente MQTT Assíncrono para Telemetria IoT
Implementa comunicação via protocolo MQTT para recepção de dados de sensores
Disciplina: ADS - Módulo 4 - Hardware Virtual e Edge Computing
"""

import json
import logging
import threading
import time
from typing import Optional, Callable, Dict, Any
from queue import Queue

logger = logging.getLogger(__name__)

# Tópicos MQTT
TOPIC_TELEMETRIA = "redevita/sensores/+/telemetria"


class MQTTClientHandler:
    """
    Handler para cliente MQTT com tratamento de fallback.
    Processa mensagens de telemetria de forma assíncrona.
    """
    
    def __init__(self, broker_host: str = "localhost", broker_port: int = 1883, 
                 client_id: str = "redevita_backend", use_mqtt: bool = False):
        """
        Inicializa o handler MQTT.
        
        Args:
            broker_host: Host do broker MQTT
            broker_port: Porta do broker MQTT
            client_id: ID do cliente MQTT
            use_mqtt: Se deve tentar conectar ao broker (fallback para False se indisponível)
        """
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client_id = client_id
        self.use_mqtt = use_mqtt
        self.client = None
        self.connected = False
        self.message_queue = Queue()
        self.processing_thread = None
        self.running = False
        
        # Callbacks customizáveis
        self.on_message_callback: Optional[Callable] = None
        
        # Tenta importar paho-mqtt
        self.paho_available = False
        try:
            import paho.mqtt.client as mqtt
            self.mqtt = mqtt
            self.paho_available = True
            logger.info("Biblioteca paho-mqtt disponível")
        except ImportError:
            logger.warning("Biblioteca paho-mqtt não instalada. MQTT desabilitado.")
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback de conexão MQTT."""
        if rc == 0:
            self.connected = True
            logger.info(f"MQTT Client conectado ao broker {self.broker_host}:{self.broker_port}")
            # Subscribe no tópico de telemetria
            client.subscribe(TOPIC_TELEMETRIA)
            logger.info(f"Inscrito no tópico: {TOPIC_TELEMETRIA}")
        else:
            logger.error(f"Falha na conexão MQTT. Código: {rc}")
    
    def _on_message(self, client, userdata, msg):
        """Callback de recebimento de mensagem MQTT."""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            logger.debug(f"Mensagem MQTT recebida em {topic}: {payload}")
            
            # Parse JSON payload
            data = json.loads(payload)
            
            # Extrai device_id do tópico (redevita/sensores/{device_id}/telemetria)
            topic_parts = topic.split('/')
            device_id = topic_parts[2] if len(topic_parts) > 2 else "unknown"
            
            # Adiciona device_id aos dados
            data['dispositivo_id'] = data.get('dispositivo_id', device_id)
            
            # Coloca na fila para processamento assíncrono
            self.message_queue.put(data)
            
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar JSON MQTT: {e}")
        except Exception as e:
            logger.error(f"Erro ao processar mensagem MQTT: {e}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback de desconexão MQTT."""
        self.connected = False
        if rc != 0:
            logger.warning(f"MQTT Client desconectado inesperadamente. Código: {rc}")
    
    def _process_messages(self):
        """Thread de processamento de mensagens da fila."""
        logger.info("Thread de processamento MQTT iniciada")
        
        while self.running:
            try:
                # Timeout de 1 segundo para permitir verificação de running
                data = self.message_queue.get(timeout=1.0)
                
                # Processa a mensagem
                if self.on_message_callback:
                    self.on_message_callback(data)
                
                self.message_queue.task_done()
                
            except Exception as e:
                if self.running:
                    logger.error(f"Erro ao processar mensagem da fila: {e}")
                time.sleep(0.1)
        
        logger.info("Thread de processamento MQTT encerrada")
    
    def connect(self) -> bool:
        """
        Conecta ao broker MQTT.
        
        Returns:
            True se conectado com sucesso, False caso contrário
        """
        if not self.paho_available or not self.use_mqtt:
            logger.info("MQTT desabilitado (biblioteca não disponível ou configurado como False)")
            return False
        
        try:
            self.client = self.mqtt.Client(client_id=self.client_id)
            self.client.on_connect = self._on_connect
            self.client.on_message = self._on_message
            self.client.on_disconnect = self._on_disconnect
            
            logger.info(f"Tentando conectar ao broker MQTT {self.broker_host}:{self.broker_port}...")
            self.client.connect(self.broker_host, self.broker_port, keepalive=60)
            
            # Inicia loop em thread separada
            self.client.loop_start()
            
            # Aguarda conexão (timeout de 5 segundos)
            timeout = 5
            start_time = time.time()
            while not self.connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            if self.connected:
                logger.info("MQTT Client conectado com sucesso")
                return True
            else:
                logger.warning("Timeout ao conectar ao broker MQTT")
                self.client.loop_stop()
                return False
                
        except Exception as e:
            logger.error(f"Erro ao conectar ao broker MQTT: {e}")
            return False
    
    def start(self, message_callback: Optional[Callable] = None):
        """
        Inicia o handler MQTT.
        
        Args:
            message_callback: Callback para processar mensagens recebidas
        """
        self.on_message_callback = message_callback
        self.running = True
        
        # Tenta conectar ao broker
        if self.connect():
            logger.info("MQTT Client iniciado com broker conectado")
        else:
            logger.info("MQTT Client iniciado em modo fallback (sem broker)")
        
        # Inicia thread de processamento
        self.processing_thread = threading.Thread(target=self._process_messages, daemon=True)
        self.processing_thread.start()
    
    def stop(self):
        """Para o handler MQTT."""
        logger.info("Parando MQTT Client...")
        self.running = False
        
        if self.processing_thread:
            self.processing_thread.join(timeout=2.0)
        
        if self.client and self.connected:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("MQTT Client desconectado")
    
    def publish_message(self, topic: str, payload: Dict[str, Any], qos: int = 0) -> bool:
        """
        Publica uma mensagem MQTT (opcional para comandos).
        
        Args:
            topic: Tópico MQTT
            payload: Dados a publicar (serão convertidos para JSON)
            qos: Quality of Service (0, 1, ou 2)
            
        Returns:
            True se publicado com sucesso, False caso contrário
        """
        if not self.connected or not self.client:
            logger.warning("Tentativa de publicar MQTT sem conexão")
            return False
        
        try:
            payload_json = json.dumps(payload)
            self.client.publish(topic, payload_json, qos=qos)
            logger.debug(f"Mensagem publicada em {topic}")
            return True
        except Exception as e:
            logger.error(f"Erro ao publicar mensagem MQTT: {e}")
            return False
    
    def is_connected(self) -> bool:
        """Verifica se está conectado ao broker."""
        return self.connected


# Instância global do handler MQTT
_mqtt_handler: Optional[MQTTClientHandler] = None


def get_mqtt_handler() -> MQTTClientHandler:
    """
    Obtém a instância global do handler MQTT.
    Cria se não existir.
    """
    global _mqtt_handler
    if _mqtt_handler is None:
        # Lê configurações do ambiente
        import os
        broker_host = os.environ.get('MQTT_BROKER_HOST', 'localhost')
        broker_port = int(os.environ.get('MQTT_BROKER_PORT', '1883'))
        use_mqtt = os.environ.get('USE_MQTT', 'false').lower() == 'true'
        
        _mqtt_handler = MQTTClientHandler(
            broker_host=broker_host,
            broker_port=broker_port,
            use_mqtt=use_mqtt
        )
    
    return _mqtt_handler


def iniciar_mqtt_handler(message_callback: Optional[Callable] = None):
    """
    Inicia o handler MQTT global.
    
    Args:
        message_callback: Callback para processar mensagens
    """
    handler = get_mqtt_handler()
    handler.start(message_callback)


def parar_mqtt_handler():
    """Para o handler MQTT global."""
    global _mqtt_handler
    if _mqtt_handler:
        _mqtt_handler.stop()
