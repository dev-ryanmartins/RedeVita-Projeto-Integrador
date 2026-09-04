# RedeVita

Sistema de gestão de medicamentos e doações, desenvolvido para facilitar o controle de estoque, rastreabilidade de doações e conformidade regulatória (ANVISA / Portaria 344).

## Estrutura do projeto

```
redevita/
├── backend/                  # Aplicação Flask (servidor)
│   ├── main.py               # Ponto de entrada / factory da app
│   ├── requirements.txt      # Dependências Python (referência)
│   └── app/
│       ├── config.py         # Configurações (SECRET_KEY, DB, Mail)
│       ├── database.py       # SQLAlchemy, Migrate, seed ANVISA
│       ├── extensions.py     # Flask-Limiter
│       ├── core/
│       │   ├── security.py   # Hash de senha
│       │   └── decorators.py # @admin_required
│       ├── models/           # Modelos SQLAlchemy
│       │   ├── usuario.py
│       │   ├── medicamento.py
│       │   ├── medicamento_referencia.py
│       │   ├── doacao.py
│       │   ├── paciente.py
│       │   ├── medico.py
│       │   ├── farmacia.py
│       │   ├── receita.py
│       │   └── log_atividade.py
│       ├── routes/           # Blueprints Flask
│       │   ├── auth.py
│       │   ├── inventory.py
│       │   ├── donation.py
│       │   ├── pacientes.py
│       │   ├── medicos.py
│       │   ├── farmacias.py
│       │   ├── relatorios.py
│       │   ├── logs.py
│       │   ├── usuarios.py
│       │   └── mapa.py
│       ├── schemas/          # Validadores de entrada
│       │   ├── user_schema.py
│       │   └── med_schema.py
│       └── utils/
│           ├── log_helper.py
│           ├── semaforo.py   # Status de validade
│           └── validators.py
├── frontend/                 # Assets estáticos e templates Jinja2
│   ├── templates/            # HTML (herança de base.html)
│   └── static/
│       ├── css/              # Estilos por módulo
│       ├── js/               # mascaras.js, chart.umd.min.js
│       └── img/              # Imagens
├── instance/                 # Banco SQLite local (ignorado no git)
├── pyproject.toml            # Dependências gerenciadas pelo uv
├── Procfile                  # Deploy produção (gunicorn)
└── .env.example              # Variáveis de ambiente necessárias
```

## Como rodar

No Replit, as dependências Python são instaladas a partir das declarações do
projeto e o workflow `Start application` inicia o servidor automaticamente.
O workflow executa:

```bash
APP_HOST=0.0.0.0 PORT=5000 APP_DEBUG=false OPEN_BROWSER=false python main.py
```

Para iniciar manualmente em um ambiente local:

```bash
python main.py
```

O servidor fica disponível na porta `5000`. O banco SQLite local é criado em
`instance/redevita.db` quando `DATABASE_URL` não está definida.

## Credenciais padrão (desenvolvimento)

- **CPF:** `00000000000`
- **Senha:** `admin123`
- **Cargo:** Admin

## Variáveis de ambiente

Copie `.env.example` para `.env` e preencha:

| Variável | Descrição |
|---|---|
| `SECRET_KEY` | Chave secreta Flask (troque em produção) |
| `DATABASE_URL` | URL PostgreSQL (opcional; usa SQLite se ausente) |
| `MAIL_*` | Configurações SMTP para recuperação de senha |

## User preferences

- Linguagem do sistema: Português (Brasil)
- Banco de desenvolvimento: SQLite (instance/redevita.db)
- Banco de produção: PostgreSQL via DATABASE_URL
