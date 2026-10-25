# Banco de Dados - Setup e Teste

## Banco Local de Desenvolvimento

O projeto usa SQLite como banco padrão. O banco é criado automaticamente na primeira execução.

### Localização

- **Banco de desenvolvimento:** `backend/instance/redevita.db` (padrão)
- **Banco de teste:** Pode ser configurado via `SQLALCHEMY_DATABASE_URI` ou usar banco in-memory em testes

### Arquivos Temporários do SQLite

O SQLite pode criar arquivos temporários durante a execução:
- `*.db-wal`: Write-Ahead Log (WAL) - arquivo de log para gravação
- `*.db-shm`: Shared Memory - arquivo de memória compartilhada

Esses arquivos são artefatos de execução e **não devem ser versionados no Git**. Eles são regenerados automaticamente pelo SQLite quando necessário.

## Criar Banco de Teste Limpo com Dados Sintéticos

### Opção 1: Usar Banco In-Memory (Testes Automatizados)

Para testes automatizados, use banco in-memory (sem persistência):

```python
from app.main import create_app

app = create_app({
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
    'TESTING': True
})

with app.app_context():
    db.create_all()
    # Inserir dados sintéticos
    ...
```

### Opção 2: Usar Banco Descartável em Arquivo

Para testes manuais ou benchmark, crie um banco descartável:

```python
import sys
sys.path.insert(0, 'backend')
from app.main import create_app
from app.database import db
from app.models.usuario import Usuario
from app.models.medicamento import Medicamento
from app.core.security import criptografar_senha
from datetime import date

# Criar app com banco descartável
app = create_app({'SQLALCHEMY_DATABASE_URI': 'sqlite:///instance/test.db'})

with app.app_context():
    db.create_all()
    
    # Inserir dados sintéticos
    usuario = Usuario(
        nome='Usuario Teste',
        cpf='12345678900',
        email='teste@teste.com',
        senha=criptografar_senha('senha123'),
        cargo='Admin',
        ativo=True
    )
    db.session.add(usuario)
    
    medicamento = Medicamento(
        nome='Medicamento Teste',
        principio_ativo='Principio Teste',
        tarja='Sem Tarja',
        quantidade=100,
        data_validade=date(2026, 12, 31),
        lote='L0001',
        status_semaforo=0
    )
    db.session.add(medicamento)
    
    db.session.commit()
```

### Limpar Banco de Teste

Após o teste, remova o banco descartável:

```bash
rm backend/instance/test.db
```

## Migrations

O projeto usa Flask-SQLAlchemy com `db.create_all()` para criar tabelas. Para uso em produção com migrations versionadas, configure Flask-Migrate:

```bash
# Inicializar migrations (primeira vez)
flask db init

# Criar migration
flask db migrate -m "Descrição da migration"

# Aplicar migration
flask db upgrade
```

Veja `backend/MIGRATIONS.md` para mais detalhes.

## Banco de Produção

Para produção, use PostgreSQL ou MySQL configurado via variável de ambiente:

```bash
export DATABASE_URL="postgresql://usuario:senha@host:porta/banco"
# ou
export DATABASE_URL="mysql+pymysql://usuario:senha@host:porta/banco"
```

**Importante:**
- Nunca use banco SQLite em produção
- Nunca versione bancos de produção no Git
- Nunca commit arquivos WAL/SHM do SQLite
- Nunca exponha credenciais de banco em código ou commits

## Backup e Restauração

Para bancos descartáveis de teste, use o script fornecido:

```bash
# Backup
python scripts/backup_restore_sqlite.py backup

# Restauração
python scripts/backup_restore_sqlite.py restore

# Validação
python scripts/backup_restore_sqlite.py validate
```

Para bancos de produção, use ferramentas específicas do banco:
- PostgreSQL: `pg_dump` / `pg_restore`
- MySQL: `mysqldump` / `mysql`

## Acesso Inicial

Após criar o banco, o sistema cria automaticamente um usuário administrador inicial:

- **CPF:** `000.000.000-00`
- **Senha:** `admin123`
- **Cargo:** Admin

**Importante:** Este usuário é criado apenas se o banco estiver vazio. Em produção, provisione usuários de forma segura e exija troca de senha no primeiro login.
