#!/usr/bin/env python3
"""
Script para testar a conexão com o banco de dados
"""

import os
import sys

# Adiciona o diretório backend ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import Config
from app.database import db
from flask import Flask

def main():
    """Função principal para testar a conexão"""
    print("=" * 70)
    print("🔍 TESTANDO CONEXÃO COM O BANCO DE DADOS - RedeVita")
    print("=" * 70)
    print()
    
    # Cria uma aplicação Flask simples
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Inicializa o banco de dados
    db.init_app(app)
    
    with app.app_context():
        try:
            # Testa a conexão
            print("📋 Conectando ao banco de dados...")
            connection = db.engine.connect()
            print("✅ Conexão estabelecida com sucesso!")
            print()
            
            # Exibe informações da conexão
            print("📊 INFORMAÇÕES DA CONEXÃO:")
            print(f"   URL do Banco: {db.engine.url}")
            print(f"   Driver: {db.engine.driver}")
            print()
            
            # Lista as tabelas
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"📋 Tabelas encontradas: {len(tables)}")
            for table in sorted(tables):
                print(f"   - {table}")
            print()
            
            # Testa uma query simples
            print("🔍 Executando query de teste...")
            result = connection.execute(db.text("SELECT 1"))
            print(f"✅ Query executada com sucesso! Resultado: {result.fetchone()}")
            print()
            
            connection.close()
            
            print("=" * 70)
            print("✅ TESTE DE CONEXÃO CONCLUÍDO COM SUCESSO")
            print("=" * 70)
            
        except Exception as e:
            print(f"❌ ERRO ao testar conexão: {str(e)}")
            print()
            print("💡 Verifique:")
            print("   1. Se o arquivo .env está configurado corretamente")
            print("   2. Se o servidor MySQL está rodando")
            print("   3. Se as credenciais de acesso estão corretas")
            print("   4. Se o banco de dados 'redevita' existe no MySQL")
            print()
            sys.exit(1)

if __name__ == "__main__":
    main()
