"""
Predictive Stock - Módulo de Predição de Demanda e Estoque Futuro
Algoritmo que analisa histórico de entradas e saídas para prever esgotamento
Implementa Min-Heap para FEFO (First Expire, First Out) - O(1) acesso ao medicamento mais próximo do vencimento
"""

import heapq
from datetime import datetime, date, timedelta
from typing import Dict, List, Tuple
from sqlalchemy import func
from app.database import db
from app.models.medicamento import Medicamento
from app.models.doacao import Doacao


class PredictiveStockAnalyzer:
    """Analisador preditivo de estoque com Min-Heap para FEFO"""
    
    def __init__(self):
        self.DAYS_TO_ANALYZE = 30  # Período de análise em dias
        self.MIN_SAMPLES = 3  # Mínimo de amostras para cálculo
        self._fefo_heap = []  # Min-Heap para ordenação por validade
        self._heap_initialized = False
    
    def calculate_daily_consumption(self, medicamento_id: int) -> float:
        """
        Calcula o consumo médio diário de um medicamento
        baseado nas doações dos últimos N dias
        """
        cutoff_date = datetime.now() - timedelta(days=self.DAYS_TO_ANALYZE)
        
        # Soma das quantidades doadas no período
        total_consumed = db.session.query(
            func.sum(Doacao.quantidade)
        ).filter(
            Doacao.medicamento_id == medicamento_id,
            Doacao.data_doacao >= cutoff_date
        ).scalar() or 0
        
        # Consumo médio diário
        daily_consumption = total_consumed / self.DAYS_TO_ANALYZE
        
        return daily_consumption
    
    def calculate_days_until_empty(self, current_quantity: int, daily_consumption: float) -> int:
        """
        Calcula dias até esgotamento do estoque
        """
        if daily_consumption <= 0:
            return 999  # Indica estoque estável ou sem consumo
        
        days_until_empty = current_quantity / daily_consumption
        return int(days_until_empty)
    
    def predict_stock_status(self, medicamento: Medicamento) -> Dict:
        """
        Prediz o status futuro do estoque de um medicamento
        """
        daily_consumption = self.calculate_daily_consumption(medicamento.id)
        days_until_empty = self.calculate_days_until_empty(
            medicamento.quantidade, 
            daily_consumption
        )
        
        # Classificação do risco
        if days_until_empty <= 7:
            risk_level = 'critical'
            risk_label = 'Crítico - Esgotamento iminente'
        elif days_until_empty <= 14:
            risk_level = 'high'
            risk_label = 'Alto - Esgotamento em até 2 semanas'
        elif days_until_empty <= 30:
            risk_level = 'medium'
            risk_label = 'Médio - Esgotamento em até 1 mês'
        elif days_until_empty <= 90:
            risk_level = 'low'
            risk_label = 'Baixo - Estoque suficiente'
        else:
            risk_level = 'stable'
            risk_label = 'Estável - Estoque abundante'
        
        # Data prevista de esgotamento
        if days_until_empty < 999:
            empty_date = date.today() + timedelta(days=days_until_empty)
        else:
            empty_date = None
        
        return {
            'medicamento_id': medicamento.id,
            'nome': medicamento.nome,
            'lote': medicamento.lote,
            'quantidade_atual': medicamento.quantidade,
            'consumo_diario_medio': round(daily_consumption, 2),
            'dias_autonomia': days_until_empty,
            'data_esgotamento_prevista': empty_date.isoformat() if empty_date else None,
            'nivel_risco': risk_level,
            'rotulo_risco': risk_label,
            'validade': medicamento.data_validade.isoformat() if medicamento.data_validade else None,
            'status_semaforo': medicamento.status_semaforo
        }
    
    def analyze_all_medicamentos(self) -> List[Dict]:
        """
        Analisa todos os medicamentos e retorna predições
        """
        medicamentos = Medicamento.query.all()
        predictions = []
        
        for medicamento in medicamentos:
            prediction = self.predict_stock_status(medicamento)
            predictions.append(prediction)
        
        # Ordena por dias de autonomia (menor primeiro)
        predictions.sort(key=lambda x: x['dias_autonomia'])
        
        return predictions
    
    def get_critical_medicamentos(self, limit: int = 10) -> List[Dict]:
        """
        Retorna medicamentos com risco crítico de esgotamento
        """
        all_predictions = self.analyze_all_medicamentos()
        critical = [p for p in all_predictions if p['nivel_risco'] in ['critical', 'high']]
        return critical[:limit]
    
    def get_stock_summary(self) -> Dict:
        """
        Retorna um resumo geral do estoque preditivo
        """
        all_predictions = self.analyze_all_medicamentos()
        
        critical_count = len([p for p in all_predictions if p['nivel_risco'] == 'critical'])
        high_risk_count = len([p for p in all_predictions if p['nivel_risco'] == 'high'])
        medium_risk_count = len([p for p in all_predictions if p['nivel_risco'] == 'medium'])
        low_risk_count = len([p for p in all_predictions if p['nivel_risco'] == 'low'])
        stable_count = len([p for p in all_predictions if p['nivel_risco'] == 'stable'])
        
        total_medicamentos = len(all_predictions)
        
        # Média de dias de autonomia
        avg_autonomy = sum(p['dias_autonomia'] for p in all_predictions) / total_medicamentos if total_medicamentos > 0 else 0
        
        return {
            'total_medicamentos': total_medicamentos,
            'critico': critical_count,
            'alto_risco': high_risk_count,
            'medio_risco': medium_risk_count,
            'baixo_risco': low_risk_count,
            'estavel': stable_count,
            'media_dias_autonomia': round(avg_autonomy, 1),
            'medicamentos_mais_criticos': self.get_critical_medicamentos(5)
        }
    
    def _initialize_fefo_heap(self):
        """
        Inicializa o Min-Heap FEFO (First Expire, First Out).
        Ordena medicamentos por data de validade ascendente.
        Complexidade: O(n) para construção inicial.
        """
        if self._heap_initialized:
            return
        
        medicamentos = Medicamento.query.filter(
            Medicamento.quantidade > 0,
            Medicamento.data_validade >= date.today()
        ).all()
        
        # Constrói heap: (data_validade, id, medicamento)
        # heapq.heappush é O(log n), mas heapify é O(n)
        self._fefo_heap = [
            (med.data_validade, med.id, med)
            for med in medicamentos
        ]
        heapq.heapify(self._fefo_heap)
        self._heap_initialized = True
    
    def get_next_expiring_medication(self) -> Dict:
        """
        Retorna o medicamento com a data de validade mais próxima (FEFO).
        Complexidade: O(1) para acesso ao topo do heap.
        
        Returns:
            Dict com informações do medicamento ou None se heap vazio
        """
        self._initialize_fefo_heap()
        
        if not self._fefo_heap:
            return None
        
        # Peek no topo do heap (sem remover) - O(1)
        validade, med_id, medicamento = self._fefo_heap[0]
        
        # Verifica se ainda tem estoque
        if medicamento.quantidade <= 0:
            heapq.heappop(self._fefo_heap)  # Remove se sem estoque
            return self.get_next_expiring_medication()  # Recursivo para próximo
        
        return {
            'id': medicamento.id,
            'nome': medicamento.nome,
            'lote': medicamento.lote,
            'data_validade': medicamento.data_validade.isoformat(),
            'quantidade': medicamento.quantidade,
            'dias_para_vencer': (medicamento.data_validade - date.today()).days
        }
    
    def pop_next_expiring(self) -> Dict:
        """
        Remove e retorna o medicamento com validade mais próxima.
        Usado quando o medicamento é dispensado.
        Complexidade: O(log n) para remoção do heap.
        
        Returns:
            Dict com informações do medicamento removido
        """
        self._initialize_fefo_heap()
        
        if not self._fefo_heap:
            return None
        
        validade, med_id, medicamento = heapq.heappop(self._fefo_heap)
        
        return {
            'id': medicamento.id,
            'nome': medicamento.nome,
            'lote': medicamento.lote,
            'data_validade': medicamento.data_validade.isoformat(),
            'quantidade': medicamento.quantidade
        }
    
    def add_to_fefo_heap(self, medicamento: Medicamento):
        """
        Adiciona um novo medicamento ao heap FEFO.
        Usado quando novo estoque é adicionado.
        Complexidade: O(log n) para inserção.
        
        Args:
            medicamento: Objeto Medicamento a adicionar
        """
        heapq.heappush(
            self._fefo_heap,
            (medicamento.data_validade, medicamento.id, medicamento)
        )
    
    def get_expiring_soon(self, days: int = 30) -> List[Dict]:
        """
        Retorna todos os medicamentos que vencem nos próximos N dias.
        Usa o heap para busca eficiente.
        
        Args:
            days: Número de dias à frente para verificar
        
        Returns:
            Lista de medicamentos próximos ao vencimento
        """
        self._initialize_fefo_heap()
        
        cutoff_date = date.today() + timedelta(days=days)
        expiring_soon = []
        
        # Cria uma cópia do heap para não modificar o original
        temp_heap = self._fefo_heap.copy()
        heapq.heapify(temp_heap)
        
        while temp_heap:
            validade, med_id, medicamento = heapq.heappop(temp_heap)
            if validade <= cutoff_date and medicamento.quantidade > 0:
                expiring_soon.append({
                    'id': medicamento.id,
                    'nome': medicamento.nome,
                    'lote': medicamento.lote,
                    'data_validade': validade.isoformat(),
                    'quantidade': medicamento.quantidade,
                    'dias_para_vencer': (validade - date.today()).days
                })
            elif validade > cutoff_date:
                # Como o heap está ordenado, podemos parar
                break
        
        return expiring_soon


def get_stock_prediction(medicamento_id: int = None) -> Dict:
    """
    Função auxiliar para obter predição de estoque
    Se medicamento_id for fornecido, retorna predição específica
    Caso contrário, retorna análise completa
    """
    analyzer = PredictiveStockAnalyzer()
    
    if medicamento_id:
        medicamento = Medicamento.query.get(medicamento_id)
        if medicamento:
            return analyzer.predict_stock_status(medicamento)
        return None
    
    return analyzer.analyze_all_medicamentos()


def get_stock_summary() -> Dict:
    """
    Função auxiliar para obter resumo do estoque
    """
    analyzer = PredictiveStockAnalyzer()
    return analyzer.get_stock_summary()
