"""
Geo Graph - Algoritmo de Grafos para Micrologística
Implementa Grafo com algoritmo de Dijkstra para calcular rota ótima entre farmácias e pacientes
Disciplina: Estruturas de Dados - Grafos e Algoritmos de Caminho Mínimo
"""

import heapq
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from app.models.farmacia import Farmacia


@dataclass
class NoGrafo:
    """
    Nó do Grafo representando uma farmácia ou ponto de coleta.
    """
    id: int
    nome: str
    tipo: str  # 'farmacia', 'posto_coleta', 'paciente'
    latitude: float
    longitude: float


@dataclass
class Aresta:
    """
    Aresta do Grafo representando a distância entre dois nós.
    """
    origem: int
    destino: int
    peso: float  # Distância em km


class Grafo:
    """
    Estrutura de Dados Grafo para representar a rede de farmácias e pontos de coleta.
    Implementa algoritmo de Dijkstra para encontrar o caminho mais curto.
    """
    
    def __init__(self):
        self.nos: Dict[int, NoGrafo] = {}
        self.arestas: Dict[int, List[Tuple[int, float]]] = {}  # {origem: [(destino, peso), ...]}
    
    def adicionar_no(self, no: NoGrafo):
        """
        Adiciona um nó ao grafo.
        """
        self.nos[no.id] = no
        if no.id not in self.arestas:
            self.arestas[no.id] = []
    
    def adicionar_aresta(self, origem_id: int, destino_id: int, peso: float):
        """
        Adiciona uma aresta não direcionada ao grafo.
        """
        if origem_id not in self.arestas:
            self.arestas[origem_id] = []
        if destino_id not in self.arestas:
            self.arestas[destino_id] = []
        
        self.arestas[origem_id].append((destino_id, peso))
        self.arestas[destino_id].append((origem_id, peso))  # Grafo não direcionado
    
    def calcular_distancia_haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calcula a distância entre dois pontos geográficos usando a fórmula de Haversine.
        
        Args:
            lat1, lon1: Coordenadas do primeiro ponto
            lat2, lon2: Coordenadas do segundo ponto
        
        Returns:
            Distância em quilômetros
        """
        from math import radians, sin, cos, sqrt, asin
        
        R = 6371  # Raio da Terra em km
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))
        
        return R * c
    
    def dijkstra(self, origem_id: int, destino_id: int) -> Tuple[float, List[int]]:
        """
        Algoritmo de Dijkstra para encontrar o caminho mais curto.
        Complexidade: O((V + E) log V) usando heap binário.
        
        Args:
            origem_id: ID do nó de origem
            destino_id: ID do nó de destino
        
        Returns:
            Tupla com (distância total, lista de IDs do caminho)
        """
        if origem_id not in self.nos or destino_id not in self.nos:
            return float('inf'), []
        
        # Inicialização
        distancias: Dict[int, float] = {no_id: float('inf') for no_id in self.nos}
        distancias[origem_id] = 0
        anteriores: Dict[int, Optional[int]] = {no_id: None for no_id in self.nos}
        visitados: Set[int] = set()
        
        # Heap de prioridade (distância, nó)
        heap = [(0, origem_id)]
        
        while heap:
            distancia_atual, no_atual = heapq.heappop(heap)
            
            if no_atual in visitados:
                continue
            
            visitados.add(no_atual)
            
            if no_atual == destino_id:
                break
            
            for vizinho, peso in self.arestas.get(no_atual, []):
                if vizinho in visitados:
                    continue
                
                nova_distancia = distancia_atual + peso
                
                if nova_distancia < distancias[vizinho]:
                    distancias[vizinho] = nova_distancia
                    anteriores[vizinho] = no_atual
                    heapq.heappush(heap, (nova_distancia, vizinho))
        
        # Reconstrói o caminho
        if distancias[destino_id] == float('inf'):
            return float('inf'), []
        
        caminho = []
        no = destino_id
        while no is not None:
            caminho.append(no)
            no = anteriores[no]
        
        caminho.reverse()
        
        return distancias[destino_id], caminho
    
    def encontrar_farmacia_proxima(self, paciente_lat: float, paciente_lon: float) -> Tuple[Optional[NoGrafo], float]:
        """
        Encontra a farmácia mais próxima de uma localização do paciente.
        
        Args:
            paciente_lat: Latitude do paciente
            paciente_lon: Longitude do paciente
        
        Returns:
            Tupla com (farmácia mais próxima, distância em km)
        """
        farmacia_mais_proxima = None
        distancia_minima = float('inf')
        
        for no_id, no in self.nos.items():
            if no.tipo == 'farmacia':
                distancia = self.calcular_distancia_haversine(
                    paciente_lat, paciente_lon,
                    no.latitude, no.longitude
                )
                
                if distancia < distancia_minima:
                    distancia_minima = distancia
                    farmacia_mais_proxima = no
        
        return farmacia_mais_proxima, distancia_minima


# Instância global do grafo
_grafo_logistica: Optional[Grafo] = None


def construir_grafo_logistica() -> Grafo:
    """
    Constrói o grafo de logística com farmácias do banco de dados.
    Cria nós para cada farmácia e arestas baseadas em distância geográfica.
    
    Returns:
        Instância do Grafo carregado
    """
    global _grafo_logistica
    
    if _grafo_logistica is not None:
        return _grafo_logistica
    
    grafo = Grafo()
    
    # Carrega farmácias do banco
    farmacias = Farmacia.query.all()
    
    # Adiciona nós para cada farmácia
    for farmacia in farmacias:
        # Assume que Farmacia tem latitude e longitude (se não, usa valores padrão)
        lat = getattr(farmacia, 'latitude', -23.5505)  # São Paulo padrão
        lon = getattr(farmacia, 'longitude', -46.6333)
        
        no = NoGrafo(
            id=farmacia.id,
            nome=farmacia.nome_fantasia,
            tipo='farmacia',
            latitude=lat,
            longitude=lon
        )
        grafo.adicionar_no(no)
    
    # Cria arestas entre farmácias baseadas em distância
    # Conecta farmácias que estão a menos de 10km uma da outra
    farmacias_lista = list(grafo.nos.values())
    for i, farm1 in enumerate(farmacias_lista):
        for farm2 in farmacias_lista[i+1:]:
            distancia = grafo.calcular_distancia_haversine(
                farm1.latitude, farm1.longitude,
                farm2.latitude, farm2.longitude
            )
            
            if distancia <= 10.0:  # Conecta se estiver a 10km ou menos
                grafo.adicionar_aresta(farm1.id, farm2.id, distancia)
    
    _grafo_logistica = grafo
    return grafo


def calcular_rota_otima(paciente_lat: float, paciente_lon: float) -> Dict:
    """
    Calcula a rota ótima para o paciente até a farmácia mais próxima.
    
    Args:
        paciente_lat: Latitude do paciente
        paciente_lon: Longitude do paciente
    
    Returns:
        Dict com informações da rota ótima
    """
    grafo = construir_grafo_logistica()
    
    # Adiciona nó temporário para o paciente
    paciente_id = -1  # ID temporário
    no_paciente = NoGrafo(
        id=paciente_id,
        nome='Paciente',
        tipo='paciente',
        latitude=paciente_lat,
        longitude=paciente_lon
    )
    grafo.adicionar_no(no_paciente)
    
    # Conecta paciente às farmácias próximas
    for no_id, no in grafo.nos.items():
        if no.tipo == 'farmacia':
            distancia = grafo.calcular_distancia_haversine(
                paciente_lat, paciente_lon,
                no.latitude, no.longitude
            )
            
            if distancia <= 15.0:  # Conecta se estiver a 15km ou menos
                grafo.adicionar_aresta(paciente_id, no_id, distancia)
    
    # Encontra farmácia mais próxima
    farmacia_proxima, distancia = grafo.encontrar_farmacia_proxima(paciente_lat, paciente_lon)
    
    if farmacia_proxima is None:
        return {
            'sucesso': False,
            'mensagem': 'Nenhuma farmácia encontrada na região',
            'distancia': None,
            'farmacia': None
        }
    
    return {
        'sucesso': True,
        'farmacia': {
            'id': farmacia_proxima.id,
            'nome': farmacia_proxima.nome,
            'latitude': farmacia_proxima.latitude,
            'longitude': farmacia_proxima.longitude
        },
        'distancia_km': round(distancia, 2),
        'tempo_estimado_minutos': round(distancia * 3),  # Assume 20km/h média urbana
        'mensagem': f'Farmácia mais próxima a {round(distancia, 2)}km'
    }


def invalidar_grafo():
    """
    Invalida o cache do grafo, forçando reconstrução na próxima chamada.
    """
    global _grafo_logistica
    _grafo_logistica = None
