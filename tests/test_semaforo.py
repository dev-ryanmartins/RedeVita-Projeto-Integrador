"""
Test Semaforo - Suíte de Testes do Algoritmo do Semáforo
Testa o funcionamento do algoritmo de cálculo de status de validade
"""

import unittest
import sys
import os
from datetime import date, timedelta

# Adiciona o diretório backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.utils.semaforo import calcular_status_semaforo


class TestSemaforoAlgorithm(unittest.TestCase):
    """Testa o algoritmo do semáforo de validade"""
    
    def test_status_verde_validade_longa(self):
        """Testa status verde (0) para validade longa"""
        hoje = date.today()
        validade_futura = hoje + timedelta(days=60)
        status = calcular_status_semaforo(validade_futura)
        self.assertEqual(status, 0, "Validade > 30 dias deve retornar status verde (0)")
    
    def test_status_amarelo_30_dias(self):
        """Testa status amarelo (1) para validade de exatos 30 dias"""
        hoje = date.today()
        validade_30_dias = hoje + timedelta(days=30)
        status = calcular_status_semaforo(validade_30_dias)
        self.assertEqual(status, 1, "Validade de 30 dias deve retornar status amarelo (1)")
    
    def test_status_amarelo_menos_30_dias(self):
        """Testa status amarelo (1) para validade menor que 30 dias"""
        hoje = date.today()
        validade_15_dias = hoje + timedelta(days=15)
        status = calcular_status_semaforo(validade_15_dias)
        self.assertEqual(status, 1, "Validade < 30 dias deve retornar status amarelo (1)")
    
    def test_status_amarelo_1_dia(self):
        """Testa status amarelo (1) para validade de 1 dia"""
        hoje = date.today()
        validade_1_dia = hoje + timedelta(days=1)
        status = calcular_status_semaforo(validade_1_dia)
        self.assertEqual(status, 1, "Validade de 1 dia deve retornar status amarelo (1)")
    
    def test_status_vermelho_vencido_hoje(self):
        """Testa status vermelho (2) para validade vencida hoje"""
        hoje = date.today()
        validade_hoje = hoje
        status = calcular_status_semaforo(validade_hoje)
        self.assertEqual(status, 2, "Validade vencida hoje deve retornar status vermelho (2)")
    
    def test_status_vermelho_vencido_antigamente(self):
        """Testa status vermelho (2) para validade vencida há muito tempo"""
        hoje = date.today()
        validade_passada = hoje - timedelta(days=100)
        status = calcular_status_semaforo(validade_passada)
        self.assertEqual(status, 2, "Validade vencida deve retornar status vermelho (2)")
    
    def test_status_vermelho_vencido_1_dia(self):
        """Testa status vermelho (2) para validade vencida há 1 dia"""
        hoje = date.today()
        validade_ontem = hoje - timedelta(days=1)
        status = calcular_status_semaforo(validade_ontem)
        self.assertEqual(status, 2, "Validade vencida há 1 dia deve retornar status vermelho (2)")
    
    def test_limite_status_verde_amarelo(self):
        """Testa o limite exato entre verde e amarelo (31 dias)"""
        hoje = date.today()
        validade_31_dias = hoje + timedelta(days=31)
        status = calcular_status_semaforo(validade_31_dias)
        self.assertEqual(status, 0, "Validade de 31 dias deve retornar status verde (0)")
    
    def test_status_consistencia(self):
        """Testa consistência do status para diferentes datas"""
        hoje = date.today()
        
        # Testa uma sequência de datas
        test_cases = [
            (hoje + timedelta(days=100), 0),
            (hoje + timedelta(days=60), 0),
            (hoje + timedelta(days=31), 0),
            (hoje + timedelta(days=30), 1),
            (hoje + timedelta(days=15), 1),
            (hoje + timedelta(days=1), 1),
            (hoje, 2),
            (hoje - timedelta(days=1), 2),
            (hoje - timedelta(days=30), 2),
        ]
        
        for validade, expected_status in test_cases:
            status = calcular_status_semaforo(validade)
            self.assertEqual(
                status, 
                expected_status,
                f"Data {validade} deveria retornar status {expected_status}, mas retornou {status}"
            )


if __name__ == '__main__':
    unittest.main(verbosity=2)
