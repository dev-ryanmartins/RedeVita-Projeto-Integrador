# RedeVita

Sistema de gestão de medicamentos e doações com interface moderna glassmorphism, controle de acesso baseado em papéis (RBAC) e integração com Google Maps.

## Como rodar no VS Code

### Passo 1: Abrir o projeto

Abra o VS Code e selecione **File > Open Folder**, escolha a pasta do projeto.

### Passo 2: Configurar o ambiente

No terminal do VS Code (Ctrl + `), execute:

**Windows:**
```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r backend/requirements.txt
copy .env.example .env
```

**Linux/macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp .env.example .env
```

### Passo 3: Iniciar o servidor

```bash
cd backend
python main.py
```

O servidor vai rodar em `http://127.0.0.1:5000`

### Passo 4: Acessar o sistema

Abra o navegador em `http://127.0.0.1:5000`

**Login inicial:**
- CPF: `000.000.000-00`
- Senha: `admin123`

## Características

- **Interface glassmorphism moderna** com tema escuro/claro
- **RBAC (Role-Based Access Control)** para controle de acesso
- **Integração Google Maps** para visualização de farmácias
- **Integração ANVISA** para validação de medicamentos
- **Monitoramento IoT** simulado para cadeia de frio
- **Banco SQLite** local (automático)
- **Logs de auditoria** para rastreabilidade

## Estrutura do projeto

```
RedeVita-main/
├── backend/                 # Aplicação Flask
│   ├── app/
│   │   ├── core/           # Decorators, handlers, segurança
│   │   ├── models/         # Modelos do banco
│   │   ├── routes/         # Rotas da aplicação
│   │   └── utils/          # Utilitários (ANVISA, PDF, etc.)
│   └── main.py            # Arquivo principal
├── frontend/               # Interface web
│   ├── templates/          # Páginas HTML
│   └── static/             # CSS, JS, imagens
└── .env                   # Variáveis de ambiente
```
