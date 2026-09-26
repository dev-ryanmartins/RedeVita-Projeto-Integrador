#!/usr/bin/env python3
"""
Script para recriar tabelas do banco de dados usando SQLAlchemy
Este script cria todas as tabelas baseadas nos models do Flask/SQLAlchemy
"""

import os
import sys

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

def main():
    print("=" * 70)
    print("RECRIANDO TABELAS DO BANCO DE DADOS - RedeVita")
    print("=" * 70)
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

            print("ATENCAO: Todas as tabelas existentes serao DROPADAS!")
            print("Dropando tabelas existentes...")
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
