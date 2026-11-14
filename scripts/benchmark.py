#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de benchmark simples para testes de carga locais.

Este script executa um teste de carga básico em endpoints essenciais
usando dados sintéticos em ambiente descartável.

Uso:
    python scripts/benchmark.py

Limitações:
- Apenas para ambiente local de teste
- Não execute contra produção
- Não afirme que resultados locais representam produção
"""

import sys
import time
import statistics
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Adicionar backend ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.main import create_app
from app.database import db
from app.models.usuario import Usuario
from app.models.medicamento import Medicamento
from app.core.security import criptografar_senha
from datetime import date


# Configurações do benchmark
NUM_REQUESTS = 100
CONCURRENCY = 10
ENDPOINTS = [
    ('GET', '/health'),
    ('GET', '/healthz'),
]


def make_request(client, method, path):
    """Executa uma requisição HTTP e retorna status e latência."""
    start = time.time()
    try:
        if method == 'GET':
            response = client.get(path)
        elif method == 'POST':
            response = client.post(path)
        else:
            return None, None
        
        latency = time.time() - start
        return response.status_code, latency
    except Exception as e:
        latency = time.time() - start
        return None, latency


def run_benchmark():
    """Executa o benchmark."""
    print("=" * 60)
    print("BENCHMARK REDEVITA - LOCAL TEST ONLY")
    print("=" * 60)
    
    # Criar app com banco descartável (in-memory)
    print("\n1. Criando banco descartável de teste...")
    
    app = create_app({
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'TESTING': True
    })
    
    with app.app_context():
        db.create_all()
        
        # Inserir dados sintéticos
        print("   Inserindo dados sintéticos...")
        for i in range(5):
            usuario = Usuario(
                nome=f'Usuario Teste {i}',
                cpf=f'{12345678900 + i}',
                email=f'teste{i}@teste.com',
                senha=criptografar_senha('senha123'),
                cargo='Admin' if i == 0 else 'Operador',
                ativo=True
            )
            db.session.add(usuario)
        
        for i in range(10):
            medicamento = Medicamento(
                nome=f'Medicamento Teste {i}',
                principio_ativo=f'Principio {i}',
                tarja='Sem Tarja',
                quantidade=100 + i * 10,
                data_validade=date(2026, 12, 31),
                lote=f'L{i:04d}',
                status_semaforo=0
            )
            db.session.add(medicamento)
        
        db.session.commit()
        print(f"   [OK] {Usuario.query.count()} usuarios, {Medicamento.query.count()} medicamentos")
    
    # Executar benchmark
    print(f"\n2. Executando benchmark...")
    print(f"   Requisições: {NUM_REQUESTS}")
    print(f"   Concorrência: {CONCURRENCY}")
    print(f"   Endpoints: {len(ENDPOINTS)}")
    
    client = app.test_client()
    results = []
    
    for method, path in ENDPOINTS:
        print(f"\n   Testando: {method} {path}")
        latencies = []
        errors = 0
        
        with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
            futures = [
                executor.submit(make_request, client, method, path)
                for _ in range(NUM_REQUESTS)
            ]
            
            for future in as_completed(futures):
                status, latency = future.result()
                if status is not None:
                    latencies.append(latency)
                    if status >= 400:
                        errors += 1
                else:
                    errors += 1
        
        if latencies:
            p50 = statistics.median(latencies) * 1000
            p95 = statistics.quantiles(latencies, n=20)[18] * 1000 if len(latencies) >= 20 else max(latencies) * 1000
            p99 = statistics.quantiles(latencies, n=100)[98] * 1000 if len(latencies) >= 100 else max(latencies) * 1000
            avg = statistics.mean(latencies) * 1000
            
            results.append({
                'endpoint': f"{method} {path}",
                'requests': len(latencies),
                'errors': errors,
                'error_rate': (errors / NUM_REQUESTS) * 100,
                'p50_ms': round(p50, 2),
                'p95_ms': round(p95, 2),
                'p99_ms': round(p99, 2),
                'avg_ms': round(avg, 2)
            })
            
            print(f"   Requests: {len(latencies)}")
            print(f"   Errors: {errors} ({(errors/NUM_REQUESTS)*100:.2f}%)")
            print(f"   Latência p50: {p50:.2f}ms")
            print(f"   Latência p95: {p95:.2f}ms")
            print(f"   Latência p99: {p99:.2f}ms")
            print(f"   Latência média: {avg:.2f}ms")
    
    # Limpeza não necessária (banco in-memory)
    print("\n3. Banco de teste (in-memory) - limpeza não necessária")
    
    # Relatório final
    print("\n" + "=" * 60)
    print("RELATÓRIO FINAL")
    print("=" * 60)
    print(f"\nAmbiente:")
    print(f"   Python: {sys.version}")
    print(f"   Banco: SQLite (descartável)")
    print(f"   Concorrência: {CONCURRENCY}")
    print(f"   Requisições por endpoint: {NUM_REQUESTS}")
    
    print(f"\nResultados:")
    for result in results:
        print(f"\n   {result['endpoint']}:")
        print(f"     Requests: {result['requests']}")
        print(f"     Errors: {result['errors']} ({result['error_rate']:.2f}%)")
        print(f"     p50: {result['p50_ms']}ms")
        print(f"     p95: {result['p95_ms']}ms")
        print(f"     p99: {result['p99_ms']}ms")
        print(f"     Avg: {result['avg_ms']}ms")
    
    print("\n" + "=" * 60)
    print("LIMITAÇÕES:")
    print("- Este é um teste local em ambiente descartável")
    print("- Resultados não representam produção")
    print("- Não há SLA ou garantia de alta disponibilidade")
    print("- Cache, rede e banco são locais (sem latência real)")
    print("=" * 60)


if __name__ == "__main__":
    run_benchmark()
