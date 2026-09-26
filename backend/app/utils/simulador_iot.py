"""
Simulador IoT - Simulador de Dispositivos Embarcados (ESP32)
Simula microcontrolador enviando telemetria via HTTP POST para o endpoint /api/iot/telemetria
Disciplina: ADS - Módulo 4 - Internet das Coisas e Hardware Virtual

Uso via CLI:
    python -m backend.app.utils.simulador_iot --intervalo 5
    python -m backend.app.utils.simulador_iot --intervalo 10 --injetar-falha
"""

import sys
import time
import random
import argparse
import requests
import json
from datetime import datetime
from typing import Dict, List
from collections import deque


class SimuladorESP32:
    """
    Simula um dispositivo ESP32 com sensores DHT22 (temperatura/umidade).
    Envia dados de telemetria para o backend do RedeVita.
    """
    
    def __init__(self, dispositivo_id: str, farmacia_id: int = None, 
                 url_base: str = "http://localhost:5001"):
        """
        Inicializa o simulador ESP32.
        
        Args:
            dispositivo_id: ID único do dispositivo
            farmacia_id: ID da farmácia associada (opcional)
            url_base: URL base da API do RedeVita
        """
        self.dispositivo_id = dispositivo_id
        self.farmacia_id = farmacia_id
        self.url_base = url_base
        self.url_telemetria = f"{url_base}/api/iot/telemetria"
        self.url_telemetria_lote = f"{url_base}/api/iot/telemetria/lote"
        
        # Estado do simulador
        self.temperatura_base = 20.0  # Temperatura base em °C
        self.umidade_base = 55.0      # Umidade base em %
        self.injetar_falha = False    # Flag para injetar falhas
        self.rodando = False
        
        # Buffer de borda para operação offline (máximo 50 leituras)
        self.buffer_local = deque(maxlen=50)
    
    def _gerar_leitura_sensor(self) -> Dict:
        """
        Gera uma leitura simulada de temperatura, umidade e luminosidade.
        Simula variação natural dos sensores DHT22 e sensor de luz.
        
        Returns:
            Dict com temperatura, umidade e luminosidade
        """
        if self.injetar_falha:
            # Injeta falha: pico de calor (>32°C) para demonstrar alertas
            temperatura = random.uniform(30.5, 35.0)
            umidade = random.uniform(75.0, 85.0)
        else:
            # Variação normal: ±2°C da temperatura base
            temperatura = self.temperatura_base + random.uniform(-2.0, 2.0)
            # Variação normal: ±10% da umidade base
            umidade = self.umidade_base + random.uniform(-10.0, 10.0)
            
            # Limita valores a faixas realistas
            temperatura = max(15.0, min(25.0, temperatura))
            umidade = max(40.0, min(70.0, umidade))
        
        # Simula luminosidade (0-1000 lux)
        luminosidade = random.uniform(0, 800)
        
        return {
            'temperatura': round(temperatura, 2),
            'umidade': round(umidade, 2),
            'luminosidade_lux': round(luminosidade, 2)
        }
    
    def enviar_telemetria(self) -> bool:
        """
        Envia dados de telemetria para o backend.
        Se offline, armazena no buffer local.
        
        Returns:
            True se enviado com sucesso, False caso contrário
        """
        leitura = self._gerar_leitura_sensor()
        
        payload = {
            'dispositivo_id': self.dispositivo_id,
            'temperatura': leitura['temperatura'],
            'umidade': leitura['umidade'],
            'luminosidade_lux': leitura['luminosidade_lux'],
            'farmacia_id': self.farmacia_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        try:
            response = requests.post(
                self.url_telemetria,
                json=payload,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                dados = response.json()
                status = dados.get('data', {}).get('status_alerta', 'UNKNOWN')
                print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                      f"✓ Telemetria enviada: {leitura['temperatura']}°C, "
                      f"{leitura['umidade']}%, {leitura['luminosidade_lux']} lux | Status: {status}")
                
                # Tenta descarregar buffer se houver dados pendentes
                if len(self.buffer_local) > 0:
                    self.descarregar_buffer_lote()
                
                return True
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                      f"✗ Erro HTTP {response.status_code}: {response.text}")
                # Adiciona ao buffer em caso de erro
                self._adicionar_ao_buffer(payload)
                return False
                
        except requests.exceptions.ConnectionError:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                  f"✗ Erro de conexão: Servidor não respondente em {self.url_base}")
            # Adiciona ao buffer quando offline
            self._adicionar_ao_buffer(payload)
            print(f"   → Leitura armazenada no buffer local ({len(self.buffer_local)}/50)")
            return False
        except requests.exceptions.Timeout:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                  f"✗ Timeout: Servidor não respondeu em 10s")
            self._adicionar_ao_buffer(payload)
            print(f"   → Leitura armazenada no buffer local ({len(self.buffer_local)}/50)")
            return False
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                  f"✗ Erro: {str(e)}")
            self._adicionar_ao_buffer(payload)
            print(f"   → Leitura armazenada no buffer local ({len(self.buffer_local)}/50)")
            return False
    
    def _adicionar_ao_buffer(self, payload: Dict):
        """Adiciona leitura ao buffer local."""
        self.buffer_local.append(payload)
    
    def descarregar_buffer_lote(self) -> bool:
        """
        Descarrega todas as leituras do buffer local via batch dispatch.
        
        Returns:
            True se descarregado com sucesso, False caso contrário
        """
        if len(self.buffer_local) == 0:
            return True
        
        batch_payload = list(self.buffer_local)
        
        try:
            response = requests.post(
                self.url_telemetria_lote,
                json={'leituras': batch_payload},
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                dados = response.json()
                processadas = dados.get('data', {}).get('processadas', 0)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                      f"✓ Buffer descarregado: {processadas} leituras enviadas em lote")
                self.buffer_local.clear()
                return True
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                      f"✗ Erro ao descarregar buffer: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                  f"✗ Erro ao descarregar buffer: {str(e)}")
            return False
    
    def iniciar(self, intervalo_segundos: int = 5):
        """
        Inicia o loop de envio de telemetria.
        
        Args:
            intervalo_segundos: Intervalo entre envios em segundos
        """
        self.rodando = True
        print(f"\n{'='*60}")
        print(f"  Simulador ESP32 - RedeVita IoT")
        print(f"{'='*60}")
        print(f"  Dispositivo ID: {self.dispositivo_id}")
        print(f"  Farmácia ID: {self.farmacia_id if self.farmacia_id else 'Não associado'}")
        print(f"  URL: {self.url_telemetria}")
        print(f"  Intervalo: {intervalo_segundos}s")
        print(f"  Injetar Falhas: {'SIM' if self.injetar_falha else 'NÃO'}")
        print(f"{'='*60}\n")
        print("Pressione Ctrl+C para parar\n")
        
        try:
            while self.rodando:
                self.enviar_telemetria()
                time.sleep(intervalo_segundos)
        except KeyboardInterrupt:
            print(f"\n\n[{datetime.now().strftime('%H:%M:%S')}] "
                  f"Simulador interrompido pelo usuário")
            self.rodando = False
    
    def parar(self):
        """Para o simulador."""
        self.rodando = False


def main():
    """Função principal para execução via CLI."""
    parser = argparse.ArgumentParser(
        description='Simulador IoT ESP32 para RedeVita',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python -m backend.app.utils.simulador_iot --intervalo 5
  python -m backend.app.utils.simulador_iot --intervalo 10 --injetar-falha
  python -m backend.app.utils.simulador_iot --dispositivo ESP32-001 --farmacia 1
        """
    )
    
    parser.add_argument(
        '--intervalo',
        type=int,
        default=5,
        help='Intervalo entre envios em segundos (padrão: 5)'
    )
    parser.add_argument(
        '--dispositivo',
        type=str,
        default='ESP32-SIM-001',
        help='ID do dispositivo (padrão: ESP32-SIM-001)'
    )
    parser.add_argument(
        '--farmacia',
        type=int,
        default=None,
        help='ID da farmácia associada (opcional)'
    )
    parser.add_argument(
        '--url',
        type=str,
        default='http://localhost:5001',
        help='URL base da API (padrão: http://localhost:5001)'
    )
    parser.add_argument(
        '--injetar-falha',
        action='store_true',
        help='Simula picos de calor (>32°C) para demonstrar alertas'
    )
    
    args = parser.parse_args()
    
    # Cria e inicia o simulador
    simulador = SimuladorESP32(
        dispositivo_id=args.dispositivo,
        farmacia_id=args.farmacia,
        url_base=args.url
    )
    simulador.injetar_falha = args.injetar_falha
    
    try:
        simulador.iniciar(intervalo_segundos=args.intervalo)
    except Exception as e:
        print(f"\nErro fatal: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
