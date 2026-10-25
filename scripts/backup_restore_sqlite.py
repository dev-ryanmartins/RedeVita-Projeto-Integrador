#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de backup e restauração para SQLite (banco descartável de teste).

Este script fornece um procedimento reproduzível para:
1. Criar backup de banco SQLite
2. Restaurar backup em banco separado
3. Validar schema, tabelas e contagens

Uso:
    python scripts/backup_restore_sqlite.py backup
    python scripts/backup_restore_sqlite.py restore
    python scripts/backup_restore_sqlite.py validate

Pré-condições:
- SQLite3 instalado (Python sqlite3 module)
- Banco de dados original em backend/instance/redevita_test.db
- Diretório backups/ deve existir

Limitações:
- Este script é para bancos descartáveis de teste
- Não execute em produção ou banco com dados úteis
- Backup não é criptografado
- Não há versionamento incremental
"""

import sqlite3
import shutil
import os
import sys
from pathlib import Path
from datetime import datetime


# Configurações
BASE_DIR = Path(__file__).parent.parent
SOURCE_DB = BASE_DIR / "backend" / "instance" / "redevita_test.db"  # Banco descartável de teste
BACKUP_DIR = BASE_DIR / "backups"
RESTORE_DB = BASE_DIR / "backend" / "instance" / "redevita_restored.db"


def ensure_backup_dir():
    """Cria diretório de backups se não existir."""
    BACKUP_DIR.mkdir(exist_ok=True)


def backup_database():
    """Cria backup do banco de dados."""
    if not SOURCE_DB.exists():
        print(f"ERRO: Banco de dados não encontrado: {SOURCE_DB}")
        sys.exit(1)
    
    ensure_backup_dir()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"redevita_backup_{timestamp}.db"
    
    print(f"Criando backup: {SOURCE_DB} -> {backup_file}")
    shutil.copy2(SOURCE_DB, backup_file)
    
    # Verificar tamanho do backup
    backup_size = backup_file.stat().st_size
    source_size = SOURCE_DB.stat().st_size
    
    if backup_size != source_size:
        print(f"ERRO: Tamanho do backup ({backup_size} bytes) diferente do original ({source_size} bytes)")
        sys.exit(1)
    
    print(f"Backup criado com sucesso: {backup_file} ({backup_size} bytes)")
    return backup_file


def restore_database(backup_file: Path = None):
    """Restaura backup em banco separado."""
    if backup_file is None:
        # Usar o backup mais recente
        backups = sorted(BACKUP_DIR.glob("redevita_backup_*.db"))
        if not backups:
            print("ERRO: Nenhum backup encontrado")
            sys.exit(1)
        backup_file = backups[-1]
    
    if not backup_file.exists():
        print(f"ERRO: Backup não encontrado: {backup_file}")
        sys.exit(1)
    
    print(f"Restaurando backup: {backup_file} -> {RESTORE_DB}")
    shutil.copy2(backup_file, RESTORE_DB)
    
    # Verificar tamanho
    backup_size = backup_file.stat().st_size
    restore_size = RESTORE_DB.stat().st_size
    
    if restore_size != backup_size:
        print(f"ERRO: Tamanho da restauração ({restore_size} bytes) diferente do backup ({backup_size} bytes)")
        sys.exit(1)
    
    print(f"Backup restaurado com sucesso: {RESTORE_DB} ({restore_size} bytes)")
    return RESTORE_DB


def validate_database(db_path: Path):
    """Valida schema, tabelas e contagens do banco."""
    if not db_path.exists():
        print(f"ERRO: Banco não encontrado: {db_path}")
        sys.exit(1)
    
    print(f"\nValidando banco: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Verificar integridade do banco
        print("1. Verificando integridade do banco...")
        cursor.execute("PRAGMA integrity_check")
        integrity_result = cursor.fetchone()
        if integrity_result[0] != "ok":
            print(f"ERRO: Integridade do banco falhou: {integrity_result}")
            sys.exit(1)
        print("   [OK] Integridade OK")
        
        # 2. Listar tabelas
        print("\n2. Listando tabelas...")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"   Tabelas encontradas: {len(tables)}")
        for table in tables:
            print(f"   - {table}")
        
        # 3. Contar registros por tabela (sem imprimir dados)
        print("\n3. Contando registros por tabela...")
        table_counts = {}
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            table_counts[table] = count
            print(f"   - {table}: {count} registros")
        
        # 4. Verificar schema de tabelas principais
        print("\n4. Verificando schema de tabelas principais...")
        main_tables = ['usuarios', 'medicamentos', 'doacoes', 'farmacias', 'pacientes']
        for table in main_tables:
            if table in tables:
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                print(f"   - {table}: {len(columns)} colunas")
                for col in columns:
                    print(f"     {col[1]} ({col[2]})")
            else:
                print(f"   - {table}: NAO ENCONTRADA")
        
        conn.close()
        
        print("\n[OK] Validacao concluida com sucesso")
        return table_counts
        
    except Exception as e:
        print(f"ERRO: Falha na validação: {e}")
        sys.exit(1)


def main():
    """Função principal."""
    if len(sys.argv) < 2:
        print("Uso: python backup_restore_sqlite.py <backup|restore|validate> [backup_file]")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "backup":
        backup_database()
    elif command == "restore":
        backup_file = None
        if len(sys.argv) > 2:
            backup_file = Path(sys.argv[2])
        restore_database(backup_file)
    elif command == "validate":
        db_path = RESTORE_DB if RESTORE_DB.exists() else SOURCE_DB
        validate_database(db_path)
    else:
        print(f"Comando desconhecido: {command}")
        print("Uso: python backup_restore_sqlite.py <backup|restore|validate> [backup_file]")
        sys.exit(1)


if __name__ == "__main__":
    main()
