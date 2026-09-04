#!/usr/bin/env python3
"""
Backup Database Script - Script de Backup do Banco de Dados MySQL
Gera cópias de segurança do banco de dados RedeVita em formato .sql
Disciplina: DevOps & Cloud Computing - Automação de Backup Rotativo
Mantém apenas os últimos 7 backups diários para evitar sobrecarga de armazenamento
"""

import os
import sys
import subprocess
from datetime import datetime, timedelta
from pathlib import Path


def load_env():
    """Carrega variáveis de ambiente do arquivo .env"""
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()


def create_backup_directory():
    """Cria o diretório de backups se não existir"""
    backup_dir = Path(__file__).parent / 'backups'
    backup_dir.mkdir(exist_ok=True)
    return backup_dir


def generate_backup_filename():
    """Gera nome do arquivo de backup com timestamp"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"redevita_backup_{timestamp}.sql"


def perform_backup():
    """Executa o backup do banco de dados MySQL usando mysqldump"""
    # Carrega variáveis de ambiente
    load_env()
    
    # Obtém configurações do banco
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_port = os.environ.get('DB_PORT', '3306')
    db_name = os.environ.get('DB_NAME', 'redevita')
    db_user = os.environ.get('DB_USER', 'root')
    db_password = os.environ.get('DB_PASSWORD', '')
    
    # Cria diretório de backups
    backup_dir = create_backup_directory()
    backup_filename = generate_backup_filename()
    backup_path = backup_dir / backup_filename
    
    print(f"📦 Iniciando backup do banco de dados...")
    print(f"📁 Banco: {db_name}")
    print(f"🖥️  Host: {db_host}:{db_port}")
    print(f"💾 Destino: {backup_path}")
    
    # Constrói comando mysqldump
    mysqldump_cmd = [
        'mysqldump',
        f'--host={db_host}',
        f'--port={db_port}',
        f'--user={db_user}',
        f'--password={db_password}',
        '--single-transaction',
        '--routines',
        '--triggers',
        '--events',
        '--add-drop-database',
        '--databases',
        db_name
    ]
    
    try:
        # Executa o backup
        with open(backup_path, 'w', encoding='utf-8') as backup_file:
            process = subprocess.Popen(
                mysqldump_cmd,
                stdout=backup_file,
                stderr=subprocess.PIPE,
                text=True
            )
            
            _, stderr = process.communicate()
            
            if process.returncode != 0:
                print(f"❌ Erro ao executar mysqldump: {stderr}")
                return False
            
        # Comprime o arquivo com gzip se disponível
        try:
            gzip_path = backup_path.with_suffix('.sql.gz')
            with open(backup_path, 'rb') as f_in:
                import gzip
                with gzip.open(gzip_path, 'wb') as f_out:
                    f_out.writelines(f_in)
            
            # Remove o arquivo original não comprimido
            backup_path.unlink()
            backup_path = gzip_path
            print(f"✅ Backup comprimido com gzip: {backup_path}")
        except Exception as e:
            print(f"⚠️  Não foi possível comprimir o backup: {e}")
            print(f"✅ Backup não comprimido: {backup_path}")
        
        # Obtém tamanho do arquivo
        file_size = backup_path.stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        
        print(f"✅ Backup concluído com sucesso!")
        print(f"📊 Tamanho: {file_size_mb:.2f} MB")
        print(f"📂 Caminho: {backup_path}")

        # Limpeza de backups antigos (mantém os últimos 7 dias)
        cleanup_old_backups(backup_dir, keep_days=7)

        return True
        
    except FileNotFoundError:
        print("❌ Erro: mysqldump não encontrado no sistema.")
        print("💡 Instale o MySQL Client ou verifique se está no PATH")
        return False
    except Exception as e:
        print(f"❌ Erro ao criar backup: {str(e)}")
        return False


def cleanup_old_backups(backup_dir: Path, keep_days: int = 7):
    """
    Remove backups antigos, mantendo apenas os últimos N dias.
    Mantém apenas os backups dos últimos 7 dias por padrão.
    
    Args:
        backup_dir: Diretório onde os backups estão armazenados
        keep_days: Número de dias de backups a manter (padrão: 7)
    """
    try:
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        
        # Lista todos os arquivos de backup
        backup_files = list(backup_dir.glob('redevita_backup_*.sql*'))
        
        removed_count = 0
        for backup_file in backup_files:
            # Obtém data de modificação do arquivo
            file_mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
            
            # Remove se for mais antigo que o cutoff
            if file_mtime < cutoff_date:
                backup_file.unlink()
                removed_count += 1
                print(f"🗑️  Removido backup antigo: {backup_file.name} ({file_mtime.strftime('%d/%m/%Y')})")
        
        if removed_count > 0:
            print(f"✅ Limpeza concluída: {removed_count} backup(s) removido(s) (mais de {keep_days} dias)")
        else:
            print(f"✅ Nenhum backup antigo para remover (mantendo últimos {keep_days} dias)")
            
    except Exception as e:
        print(f"⚠️  Erro ao limpar backups antigos: {e}")


def list_backups():
    """Lista todos os backups disponíveis"""
    backup_dir = Path(__file__).parent / 'backups'
    
    if not backup_dir.exists():
        print("📁 Nenhum backup encontrado. Diretório de backups não existe.")
        return
    
    backup_files = sorted(
        backup_dir.glob('redevita_backup_*.sql*'),
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )
    
    if not backup_files:
        print("📁 Nenhum backup encontrado.")
        return
    
    print(f"\n📋 Backups disponíveis ({len(backup_files)}):")
    print("-" * 60)
    
    for backup_file in backup_files:
        file_size = backup_file.stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
        print(f"📄 {backup_file.name}")
        print(f"   📊 Tamanho: {file_size_mb:.2f} MB")
        print(f"   📅 Data: {mtime.strftime('%d/%m/%Y %H:%M:%S')}")
        print("-" * 60)


def restore_backup(backup_filename: str):
    """Restaura um backup específico"""
    load_env()
    
    backup_dir = Path(__file__).parent / 'backups'
    backup_path = backup_dir / backup_filename
    
    if not backup_path.exists():
        print(f"❌ Backup não encontrado: {backup_filename}")
        return False
    
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_port = os.environ.get('DB_PORT', '3306')
    db_user = os.environ.get('DB_USER', 'root')
    db_password = os.environ.get('DB_PASSWORD', '')
    
    print(f"🔄 Restaurando backup: {backup_filename}")
    
    # Descomprime se necessário
    if backup_path.suffix == '.gz':
        import gzip
        import tempfile
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.sql') as temp_file:
            with gzip.open(backup_path, 'rb') as gz_file:
                temp_file.write(gz_file.read())
            temp_path = temp_file.name
    else:
        temp_path = str(backup_path)
    
    try:
        mysql_cmd = [
            'mysql',
            f'--host={db_host}',
            f'--port={db_port}',
            f'--user={db_user}',
            f'--password={db_password}'
        ]
        
        with open(temp_path, 'r', encoding='utf-8') as backup_file:
            process = subprocess.Popen(
                mysql_cmd,
                stdin=backup_file,
                stderr=subprocess.PIPE,
                text=True
            )
            
            _, stderr = process.communicate()
            
            if process.returncode != 0:
                print(f"❌ Erro ao restaurar backup: {stderr}")
                return False
        
        print(f"✅ Backup restaurado com sucesso!")
        
        # Remove arquivo temporário se foi criado
        if backup_path.suffix == '.gz':
            os.unlink(temp_path)
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao restaurar backup: {str(e)}")
        return False


def main():
    """Função principal"""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'list':
            list_backups()
        elif command == 'restore' and len(sys.argv) > 2:
            restore_backup(sys.argv[2])
        else:
            print("Uso:")
            print("  python backup_database.py          - Criar novo backup")
            print("  python backup_database.py list      - Listar backups")
            print("  python backup_database.py restore <arquivo> - Restaurar backup")
    else:
        perform_backup()


if __name__ == '__main__':
    main()
