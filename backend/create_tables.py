#!/usr/bin/env python3
"""
Script para recriar tabelas do banco de dados usando SQLAlchemy
Este script cria todas as tabelas baseadas nos models do Flask/SQLAlchemy
"""

import os
import sys

# Adiciona o diretório backend ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import Config
from app.database import db
from flask import Flask

# Importa todos os models para registrá-los no SQLAlchemy
from app.models.usuario import Usuario
from app.models.medicamento import Medicamento
from app.models.medicamento_referencia import MedicamentoReferencia
from app.models.paciente import Paciente
from app.models.medico import Medico
from app.models.farmacia import Farmacia
from app.models.doacao import Doacao
from app.models.receita import Receita
from app.models.log_atividade import LogAtividade
from app.models.iot import LeituraIoT, TagRFID

def main():
    """Função principal para criar as tabelas"""
    print("=" * 70)
    print("🔧 RECRIANDO TABELAS DO BANCO DE DADOS - RedeVita")
    print("=" * 70)
    print()
    
    # Cria uma aplicação Flask simples apenas para configurar o banco
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Inicializa o banco de dados
    db.init_app(app)
    
    with app.app_context():
        print("📋 Verificando conexão com o banco de dados...")
        try:
            # Testa a conexão
            db.engine.connect()
            print("✅ Conexão com o banco de dados estabelecida com sucesso!")
            print()
            
            print("⚠️  ATENÇÃO: Todas as tabelas existentes serão DROPADAS!")
            print("🔨 Dropando tabelas existentes...")
            db.drop_all()
            print("✅ Tabelas dropadas com sucesso!")
            print()
            
            print("🔨 Criando tabelas baseadas nos models SQLAlchemy...")
            db.create_all()
            print("✅ Tabelas criadas com sucesso!")
            print()
            
            print("📊 Lista de tabelas criadas:")
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            for table in sorted(tables):
                print(f"  - {table}")
            print()
            
            print("=" * 70)
            print("✅ PROCESSO CONCLUÍDO COM SUCESSO")
            print("=" * 70)
            
        except Exception as e:
            print(f"❌ ERRO ao criar tabelas: {str(e)}")
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
