#!/usr/bin/env python3
"""
Script para criar tabelas do banco de dados usando SQLAlchemy
Este script cria todas as tabelas baseadas nos models do Flask/SQLAlchemy

USO NORMAL (seguro, preserva dados):
    python backend/create_tables.py

RESET DESTRUTIVO (apaga todas as tabelas e dados):
    python backend/create_tables.py --drop --confirm
    ATENÇÃO: Recusado em ambiente de produção
"""

import os
import sys
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import Config
from app.database import db
from flask import Flask

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


def is_production_environment():
    """Verifica se o ambiente atual é de produção."""
    # Verifica variável de ambiente FLASK_ENV
    flask_env = os.environ.get('FLASK_ENV', '').lower()
    if flask_env == 'production':
        return True
    
    # Verifica DATABASE_URL para identificar bancos de produção
    database_url = os.environ.get('DATABASE_URL', '')
    # URLs de produção geralmente contêm domínios específicos, não localhost
    if database_url and 'localhost' not in database_url and '127.0.0.1' not in database_url:
        return True
    
    return False


def is_safe_environment():
    """Verifica se o ambiente é seguro para operações destrutivas."""
    if is_production_environment():
        return False
    
    # Verifica se é um banco de teste ou desenvolvimento
    database_url = os.environ.get('DATABASE_URL', '')
    safe_keywords = ['test', 'dev', 'local', 'localhost', '127.0.0.1', 'sqlite']
    return any(keyword in database_url.lower() for keyword in safe_keywords)


def main():
    parser = argparse.ArgumentParser(
        description='Criar tabelas do banco de dados RedeVita',
        epilog='Por padrão, cria apenas tabelas ausentes (preserva dados). Use --drop para recriar tudo.'
    )
    parser.add_argument(
        '--drop',
        action='store_true',
        help='Modo destrutivo: apaga todas as tabelas antes de recriar'
    )
    parser.add_argument(
        '--confirm',
        action='store_true',
        help='Confirmação explícita para modo destrutivo (requerido com --drop)'
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("CRIANDO TABELAS DO BANCO DE DADOS - RedeVita")
    print("=" * 70)
    print()

    # Validação do modo destrutivo
    if args.drop:
        if not args.confirm:
            print("❌ ERRO: Modo destrutivo (--drop) requer confirmação explícita (--confirm)")
            print()
            print("Para recriar o banco de dados, execute:")
            print("  python backend/create_tables.py --drop --confirm")
            print()
            print("⚠️  AVISO: Isso apagará TODAS as tabelas e dados!")
            sys.exit(1)
        
        if is_production_environment():
            print("❌ ERRO: Operação destrutiva recusada em ambiente de produção")
            print()
            print("Detectado: FLASK_ENV=production ou DATABASE_URL de produção")
            print()
            print("Para segurança, operações destrutivas não são permitidas em produção.")
            sys.exit(1)
        
        if not is_safe_environment():
            print("⚠️  AVISO: Ambiente não identificado como seguro para operações destrutivas")
            print()
            print("Detectado DATABASE_URL:", os.environ.get('DATABASE_URL', 'não configurado'))
            print()
            print("Operações destrutivas são permitidas apenas em:")
            print("  - Ambientes de teste")
            print("  - Ambientes de desenvolvimento local")
            print("  - Bancos identificados como descartáveis")
            print()
            response = input("Deseja continuar mesmo assim? (digite 'SIM' para confirmar): ")
            if response != 'SIM':
                print("Operação cancelada pelo usuário.")
                sys.exit(1)
        
        print("⚠️  MODO DESTRUTIVO ATIVADO")
        print("   Todas as tabelas existentes serão APAGADAS!")
        print()
        response = input("Confirme a exclusão de TODOS os dados (digite 'APAGAR'): ")
        if response != 'APAGAR':
            print("Operação cancelada pelo usuário.")
            sys.exit(1)
        print()

    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    with app.app_context():
        print("Verificando conexao com o banco de dados...")
        try:
            db.engine.connect()
            print("Conexao com o banco de dados estabelecida com sucesso!")
            print()

            if args.drop:
                print("⚠️  Dropando tabelas existentes...")
                db.drop_all()
                print("Tabelas dropadas com sucesso!")
                print()

            print("Criando tabelas baseadas nos models SQLAlchemy...")
            db.create_all()
            print("Tabelas criadas com sucesso!")
            print()

            print("Lista de tabelas criadas:")
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            for table in sorted(tables):
                print(f"  - {table}")
            print()

            print("=" * 70)
            print("PROCESSO CONCLUIDO COM SUCESSO")
            print("=" * 70)

        except Exception as e:
            print(f"ERRO ao criar tabelas: {str(e)}")
            print()
            print("Verifique:")
            print("   1. Se o arquivo .env esta configurado corretamente")
            print("   2. Se o servidor MySQL esta rodando")
            print("   3. Se as credenciais de acesso estao corretas")
            print("   4. Se o banco de dados 'redevita' existe no MySQL")
            print()
            sys.exit(1)


if __name__ == "__main__":
    main()
