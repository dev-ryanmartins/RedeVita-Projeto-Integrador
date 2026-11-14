# RedeVita

**Gestão inteligente de estoque farmacêutico, prevenção de perdas e redistribuição de medicamentos para redes públicas de saúde.**

RedeVita é uma plataforma web que conecta farmácias, unidades básicas de saúde, instituições de acolhimento, médicos e pacientes em torno de um objetivo comum: **reduzir o desperdício de medicamentos** e **garantir que cada dose chegue a quem precisa, com segurança e rastreabilidade**.

---

## Visão Geral e Problema Resolvido

Redes públicas de saúde perdem recursos de duas formas principais: **medicamentos termolábeis estragam por falhas de refrigeração** e **medicamentos de uso contínuo vencem na prateleira** enquanto outras unidades passam por desabastecimento.

O RedeVita ataca essas perdas com quatro frentes integradas:

- **Monitoramento de cadeia de frio (IoT) e *Cold Crisis Lab*** — telemetria simulada de sensores de temperatura e umidade, com detecção de excursões térmicas, lacunas de leitura e simulação de cenários de crise com plano de contingência. Permite agir **antes** de perder o lote de termolábeis.
- ***Lot Rescue* + Matching Institucional** — identifica lotes próximos ao vencimento e cruza automaticamente a **oferta** das farmácias com a **necessidade** de instituições parceiras, sugerindo a redistribuição mais eficiente antes que o medicamento expire.
- **Dispensação rastreável via *QR Nonce*** — cada receita gera um QR Code de uso único e curta validade, impedindo reapresentação, clonagem ou uso indevido do documento.
- **Semáforo sanitário e auditoria** — classificação automática do estoque por risco de vencimento (verde/amarelo/vermelho), com trilha de auditoria completa de todas as operações.

---

## Arquitetura e Stack Tecnológica

| Camada | Tecnologias |
| --- | --- |
| **Backend** | Python 3.11+, Flask, SQLAlchemy (ORM), Flask-Login, JWT + Sessão, Flask-Migrate (Alembic) |
| **Frontend** | HTML5, CSS3, JavaScript (vanilla), Leaflet + OpenStreetMap |
| **Simulação IoT** | MQTT (paho-mqtt) em ambiente local/simulado |
| **Banco de Dados** | SQLite (demonstração/local) · MySQL/PostgreSQL (produção) |
| **Qualidade** | Testes automatizados com `pytest` |

**Destaques de engenharia:**

- Arquitetura em *blueprints* Flask com separação clara entre rotas, serviços de domínio e modelos.
- Controle de acesso baseado em papéis (**RBAC**) aplicado por decorators reutilizáveis.
- Respostas de API padronizadas com `correlation_id` para rastreabilidade ponta a ponta.
- Tratamento global de erros com rollback seguro de transação; nenhum *stack trace* exposto ao usuário.
- Integrações externas (CEP, e-mail, SMS) com *timeouts* curtos e *fallback* gracioso — a aplicação nunca quebra quando a rede falha.
- *Seed* de demonstração **idempotente**: pode ser executado diversas vezes sem duplicar dados.

---

## Funcionalidades Principais por Perfil

### Administrador
- Visão consolidada de estoque, doações, alertas de vencimento e indicadores operacionais.
- Painel de saúde operacional, logs de auditoria e gestão de usuários.
- Radar de integridade da telemetria IoT e relatórios da cadeia de frio.

### Farmácia
- Cadastro e gestão de lotes com classificação automática por **semáforo de validade**.
- *Janela de Resgate de Lotes* (**Lot Rescue**): projeção de tempo disponível até o vencimento.
- Criação de **ofertas** de medicamentos e confirmação de reservas para instituições.
- Triagem de doações, dispensação de receitas e baixa de estoque.

### Instituição
- Cadastro de **necessidades** de medicamentos com prioridade (urgente, alta, média).
- Recebimento de sugestões de **matching** com as ofertas disponíveis nas farmácias.
- Acompanhamento de reservas, entregas e comprovantes.

### Paciente / Médico
- Médico: emissão de receitas (incluindo receituário de controle especial) e acompanhamento.
- Paciente: consulta de receitas ativas e histórico.
- **Dispensação rastreável via QR Nonce**, com validação de uso único no ato da entrega.

---

## Como Executar Localmente

### Pré-requisitos
- Python 3.11 ou superior
- `pip` e `venv`

### 1. Clonar o repositório

```bash
git clone https://github.com/dev-ryanmartins/RedeVita-Projeto-Integrador.git
cd RedeVita-Projeto-Integrador
```

### 2. Criar e ativar o ambiente virtual

**Windows:**
```bat
python -m venv .venv
.venv\Scripts\activate
```

**Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar as dependências

```bash
pip install -r backend/requirements.txt
```

### 4. Configurar o ambiente

```bash
# Windows
copy .env.example .env

# Linux / macOS
cp .env.example .env
```

Preencha `SECRET_KEY` (mínimo 32 caracteres). Deixe `DATABASE_URL` vazio para usar o **SQLite local** automaticamente.

### 5. Popular o banco com dados de demonstração

```bash
python seed_apresentacao.py
```

O comando é **idempotente** (pode ser repetido sem duplicar dados). Use `--reset` para recriar o banco do zero. Ao final, o terminal exibe as **credenciais de login de cada perfil**.

### 6. Iniciar o servidor

```bash
python rodar.py
```

Acesse **http://127.0.0.1:5000** e faça login.

---

## Início Rápido no Windows (1 clique)

Para demonstrações e apresentações, use os scripts prontos na raiz do projeto:

| Script | Função |
| --- | --- |
| `configurar.bat` | Cria a `venv`, instala dependências e prepara o `.env`. |
| `iniciar_apresentacao.bat` | Ativa a `venv`, garante o `.env`, sobe o servidor e mostra a cola de credenciais. |
| `resetar_demo.bat` | Recria o banco do zero e roda o `seed_apresentacao.py` antes de apresentar. |

---

## Testes

```bash
pytest
```

A suíte cobre fluxos de negócio, contratos de API, segurança, validações de documentos e resiliência das integrações externas.

---

## Licença

Projeto acadêmico desenvolvido como Projeto Integrador. Uso educacional e de demonstração.
