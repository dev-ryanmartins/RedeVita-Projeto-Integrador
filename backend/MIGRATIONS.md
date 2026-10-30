# Estratégia de Migrations - RedeVita (P1.12)

## Visão Geral

O projeto RedeVita usa **Flask-Migrate** (baseado em Alembic) para gerenciar migrations de schema do banco de dados. Esta estratégia estabelece um caminho versionado e reproduzível para atualizar o schema entre ambientes.

## Ferramenta

- **Flask-Migrate 4.1.0+** (já instalado via requirements.txt)
- **Alembic 1.18.4+** (já instalado via requirements.txt)
- Compatível com SQLAlchemy 2.0+

## Banco-Alvo

**DECISÃO PENDENTE:** O banco-alvo de produção/piloto não foi definido explicitamente.

- **Desenvolvimento local:** SQLite (padrão)
- **Docker Compose:** MySQL 8.0
- **Configuração:** Aceita PostgreSQL, MySQL e SQLite via DATABASE_URL

**⚠️ IMPORTANTE:** Antes de declarar o caminho de produção concluído, o responsável deve decidir:
1. Qual banco será usado em produção (MySQL, PostgreSQL ou outro)
2. Se migrations serão validadas no mesmo tipo de banco de produção
3. A estratégia de backup e rollback para produção

## Comandos de Migration

### Criar nova migration
```bash
cd backend
flask --app main:create_app db migrate -m "descrição da mudança"
```

### Aplicar migrations (upgrade)
```bash
cd backend
flask --app main:create_app db upgrade
```

### Reverter última migration (downgrade)
```bash
cd backend
flask --app main:create_app db downgrade
```

### Verificar status
```bash
cd backend
flask --app main:create_app db current
flask --app main:create_app db history
```

## Setup Inicial

### Para banco vazio (novo projeto)
```bash
cd backend
flask --app main:create_app db upgrade
```

### Para banco existente (upgrade de schema anterior)
1. Fazer backup do banco existente
2. Testar migrations em ambiente de staging
3. Aplicar migrations: `flask --app main:create_app db upgrade`
4. Verificar aplicação
5. Validar dados preservados

## Separação de Responsabilidades

### Inicialização do Servidor
- **NÃO** aplica migrations automaticamente no startup
- `db.create_all()` no startup é seguro (cria apenas tabelas ausentes)
- `aplicar_migracoes_manuais()` foi removido do startup
- Migrations devem ser aplicadas explicitamente via comando

### Criação de Banco Vazio
- Use `flask db upgrade` para criar schema
- Ou use `python backend/create_tables.py` (P1.11 - modo seguro, sem --drop)

### Upgrade de Schema Existente
- Use `flask db upgrade` para aplicar migrations
- Nunca use `db.drop_all()` em produção
- Migrations são versionadas em `backend/migrations/versions/`

## Migrations Manuais Legadas

As migrations manuais antigas foram movidas para:
- `backend/migrations_custom/add_ativo_medicamentos.py`
- `backend/migrations_custom/necessidade_001_add_necessidades_institucionais.py`
- `backend/migrations_custom/agendamento_001_add_agendamentos_entrega.py`

Estas migrations não são mais aplicadas automaticamente. Se necessário, devem ser convertidas para Flask-Migrate.

### Necessidade Institucional

A migration `necessidade_001_add_necessidades_institucionais.py` cria a tabela `necessidades_institucionais` para o Quadro Privado de Necessidades de Instituições. Deve ser aplicada manualmente se o Flask-Migrate não estiver configurado corretamente no ambiente.

### Agendamento de Entrega

A migration `agendamento_001_add_agendamentos_entrega.py` cria a tabela `agendamentos_entrega` para o Agendamento de Entrega entre Participantes Autorizados. Deve ser aplicada manualmente se o Flask-Migrate não estiver configurado corretamente no ambiente.

## Backup e Recuperação

### Pré-requisitos para Upgrade
1. **Backup completo do banco de dados**
2. **Teste em ambiente de staging**
3. **Verificação de logs de aplicação**
4. **Plano de rollback documentado**

### Procedimento de Backup
```bash
# MySQL (exemplo via mysqldump)
mysqldump -u usuario -p nome_banco > backup_$(date +%Y%m%d_%H%M%S).sql

# PostgreSQL (exemplo via pg_dump)
pg_dump nome_banco > backup_$(date +%Y%m%d_%H%M%S).sql

# SQLite (cópia do arquivo)
cp redevita.db redevita_backup_$(date +%Y%m%d_%H%M%S).db
```

### Procedimento de Rollback
```bash
# Reverter última migration
flask --app main:create_app db downgrade

# Se necessário, restaurar do backup
mysql -u usuario -p nome_banco < backup_YYYYMMDD_HHMMSS.sql
```

## Limitações

### SQLite vs MySQL
- **SQLite em memória (testes):** Não valida comportamento de MySQL
- **MySQL:** Suporta transações, constraints e tipos diferentes
- **Validação:** Migrations devem ser testadas em MySQL se for o banco de produção

### Rollback Automático
- Alembic suporta rollback, mas nem todas as operações são reversíveis
- Exclusão de tabelas/dados não pode ser desfeita automaticamente
- Dependendo da mudança, rollback pode requerer restauração de backup

## Procedimento de Recuperação em Caso de Falha

Se uma migration falhar:

1. **Interromper e investigar:**
   - Verificar logs de erro
   - Identificar qual migration falhou
   - Verificar estado do banco

2. **Tentativas de recuperação:**
   - Tentar `flask db downgrade` se aplicável
   - Restaurar do backup se downgrade não for possível
   - Manualmente corrigir schema (último recurso)

3. **Contingência:**
   - Documentar a falha
   - Corrigir a migration
   - Testar novamente
   - Repetir o upgrade

## Decisões Pendentes

1. **Banco-alvo de produção:** MySQL ou PostgreSQL?
2. **Validação de migrations:** Testar em MySQL de produção antes de aplicar?
3. **Estratégia de backup:** Qual método de backup? Frequência?
4. **Procedimento de rollback:** Quem aprova rollback em produção?

## Documentação de Mudanças

Ao criar uma migration, documente no nome:
- O que muda (adiciona/altera/remove tabela ou coluna)
- Por que muda (motivo técnico ou requisito de negócio)
- Impacto em dados existentes (se aplica)
- Como reverter (se aplicável)

Exemplo:
```bash
flask db migrate -m "add cancelado column to doacoes for P1.4 soft deletion"
```

## Diretório de Migrations

- `backend/migrations/`: Configuração do Flask-Migrate (alembic.ini, env.py)
- `backend/migrations/versions/`: Migration scripts (gerados por Alembic)
- `backend/migrations_custom/`: Migrations manuais legadas (não aplicadas automaticamente)
- `backend/MIGRATIONS.md`: Esta documentação

**Nota:** O diretório `migrations/versions/` está no `.gitignore` para evitar conflitos entre desenvolvedores. Cada desenvolvedor deve gerar suas próprias migrations localmente e compartilhar os scripts via versionamento se necessário.
