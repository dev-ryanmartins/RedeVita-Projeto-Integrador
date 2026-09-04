# RedeVita

Sistema acadêmico em Flask para gerenciamento de medicamentos, doações, pacientes, médicos e farmácias.

## Características

- **Autenticação Avançada**: JWT tokens com hash seguro de senhas (scrypt)
- **API REST**: Endpoints JSON validados com tratamento centralizado de exceções
- **Integração Dinâmica**: fetch() assíncrono para atualização em tempo real de estoque, doações e mapas
- **Componentização UI**: Modais, formulários e alertas padronizados
- **Containerização**: Docker e docker-compose para ambiente isolado
- **CI/CD**: Pipeline automatizado com GitHub Actions

## Como rodar localmente no VS Code

O projeto usa SQLite automaticamente quando `DATABASE_URL` não está definida.
O banco fica em `instance/redevita.db`; as tabelas são criadas na primeira
execução e os dados existentes não são sobrescritos.

### Configuração automática

No Windows, abra o projeto no VS Code e execute:

```bat
configurar.bat
iniciar.bat
```

No Linux/macOS:

```bash
chmod +x configurar.sh iniciar.sh
./configurar.sh
./iniciar.sh
```

Os scripts criam `.venv`, instalam `backend/requirements.txt`, criam `.env`
a partir de `.env.example` quando necessário e iniciam o servidor na porta
`5000`.

### Configuração manual

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r backend\requirements.txt
Copy-Item .env.example .env -ErrorAction SilentlyContinue
python rodar.py
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
cp -n .env.example .env
python rodar.py
```

Também é possível iniciar diretamente com `python main.py`. No VS Code,
pressione `F5` e escolha **RedeVita - Local** para iniciar com o navegador
automático, ou **RedeVita - Debug** para iniciar sem abrir o navegador.

### Como rodar para apresentação

### Opção 1: Local (Recomendado para VS Code)

1. Configure o ambiente:
   ```bash
   configurar.bat  # Windows
   # ou ./configurar.sh no Linux/macOS
   ```

2. Execute o projeto:
   ```bash
   python rodar.py
   ```

No Windows, você também pode dar dois cliques em `iniciar.bat`.

No Linux/macOS, execute:
```bash
bash iniciar.sh
```

O inicializador local abre o navegador automaticamente em:
```text
http://localhost:5000
```

### Opção 2: VS Code Debugger

1. Abra o projeto no VS Code
2. Pressione F5 ou selecione "Run and Debug"
3. Escolha "RedeVita - Local" para rodar com navegador automático
4. Escolha "RedeVita - Debug" para modo debug sem navegador

### Opção 3: Docker

```bash
docker-compose up -d
```

Acesse: http://localhost:5000

## Login inicial

```text
CPF: 000.000.000-00
Senha: admin123
```

> Use esse usuário apenas para apresentação/local. Em um ambiente real, troque a senha imediatamente.

## Opções úteis

Por padrão, o sistema roda em `localhost:5000`. Se precisar mudar porta ou
host:

```bash
PORT=8000 python rodar.py
APP_HOST=0.0.0.0 python rodar.py
APP_DEBUG=false python rodar.py
OPEN_BROWSER=false python rodar.py
```

Para apresentação no próprio computador, prefira deixar o padrão e acessar `localhost`.

## Estrutura do Projeto

```
RedeVita-Projeto-Integrador-main/
├── backend/                 # Aplicação Flask
│   ├── app/
│   │   ├── core/           # Autenticação JWT, segurança, handlers
│   │   ├── models/         # Modelos do banco de dados
│   │   ├── routes/         # Rotas da API e páginas
│   │   └── schemas/        # Validações de entrada
│   └── requirements.txt    # Dependências Python
├── frontend/               # Templates e assets estáticos
│   ├── templates/          # Páginas HTML
│   └── static/             # CSS, JS, imagens
├── .github/workflows/      # CI/CD Pipeline
├── Dockerfile              # Configuração Docker
├── docker-compose.yml      # Orquestração de containers
├── configurar.bat         # Configuração automática no Windows
├── configurar.sh          # Configuração automática no Linux/macOS
├── iniciar.bat            # Inicialização no Windows
├── iniciar.sh             # Inicialização no Linux/macOS
└── rodar.py               # Inicializador local
```

## API Endpoints

### Autenticação
- `POST /api/auth/login` - Login com JWT
- `GET /api/auth/verificar` - Verificar token

### Inventário
- `GET /api/inventario` - Listar medicamentos
- `POST /api/inventario` - Cadastrar medicamento
- `DELETE /api/inventario/<id>` - Excluir medicamento

### Triagem
- `GET /api/triagem/recentes` - Medicamentos recentes
- `POST /api/triagem` - Registrar entrada

### Farmácias
- `GET /api/farmacias` - Listar farmácias

### Doações
- `GET /api/doacoes/recentes` - Doações recentes

## Módulos complementares

As expansões acadêmicas são aditivas e preservam as telas, rotas e modelos
existentes:

- **Monitoramento IoT:** acesse `/monitoramento-iot` para visualizar a
  simulação de temperatura e umidade dos ambientes de armazenamento. O painel
  atualiza os sensores a cada 15 segundos e também aceita atualização manual.
- **Busca rápida:** a tela de Busca Global oferece sugestões por prefixo usando
  uma Trie em `/api/v1/busca/rapida`. A busca tradicional `/buscar` continua
  sendo a consulta final e não foi substituída.
- **Auditoria complementar:** administradores podem acessar `/auditoria` para
  consultar farmácias e movimentações recentes em modo somente leitura. Os
  endpoints JSON correspondentes são `/api/v1/auditoria/farmacias` e
  `/api/v1/auditoria/movimentacoes`.

## Tema e acessibilidade

O RedeVita detecta automaticamente `prefers-color-scheme` no navegador e
inicia em modo claro ou escuro conforme a preferência do sistema. Usuários
autenticados encontram na navbar os controles para alternar o tema e aumentar
ou diminuir o tamanho da fonte; as escolhas ficam salvas no navegador. As
telas de login, cadastro, recuperação de senha e erro também respeitam o tema
e oferecem os mesmos controles quando não há navbar.

Os controles de teclado usam `focus-visible` com destaque de alto contraste,
os modais mantêm atributos ARIA e o menu responsivo informa seu estado para
leitores de tela.

## Execução via Docker

Para subir a aplicação e o MySQL integrados:

```bash
docker compose up --build
```

O serviço web fica em `http://localhost:5000` e o banco MySQL em `localhost:3306`.
Para ambientes reais, defina `SECRET_KEY`, credenciais do banco e demais
variáveis por ambiente ou por um arquivo `.env` que não seja versionado. O
healthcheck da aplicação está disponível em `/health`.
