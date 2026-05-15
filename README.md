# RedeVita

Sistema acadêmico em Flask para gerenciamento de medicamentos, doações, pacientes, médicos e farmácias.

## Como rodar para apresentação

1. Instale/configure o ambiente do projeto conforme sua máquina.
2. Execute um dos comandos abaixo na raiz do projeto:

```bash
python rodar.py
```

No Windows, você também pode dar dois cliques ou executar:

```bat
iniciar.bat
```

No Linux/macOS:

```bash
bash iniciar.sh
```

O inicializador local abre o navegador automaticamente em:

```text
http://localhost:5000
```

Assim você não precisa usar o IP da rede, como `http://192.168.x.x:5000`.


## Como usar MySQL

Se quiser apresentar usando MySQL em vez de SQLite:

1. Abra o MySQL Workbench, phpMyAdmin ou outro cliente MySQL.
2. Execute o arquivo `criar_banco_mysql.sql` completo.
3. Crie um arquivo `.env` na raiz do projeto com uma conexão parecida com:

```env
SECRET_KEY=redevita_projeto_ads_2026
DATABASE_URL=mysql+pymysql://root:SUA_SENHA@localhost:3306/redevita
```

O script SQL cria as tabelas principais, os usuários de apresentação e carrega a lista de medicamentos de referência usada pelo sistema.

Usuários criados pelo SQL, todos com senha `admin123`:

| Cargo | CPF |
|---|---|
| Admin | `000.000.000-00` |
| Operador | `111.111.111-11` |
| Médico | `222.222.222-22` |
| Farmacêutico | `333.333.333-33` |
| Voluntário | `444.444.444-44` |

## Login inicial

```text
CPF: 000.000.000-00
Senha: admin123
```

> Use esse usuário apenas para apresentação/local. Em um ambiente real, troque a senha imediatamente.

## Opções úteis

Por padrão, o sistema roda em modo debug local. Se precisar mudar porta ou host:

```bash
PORT=8000 python rodar.py
APP_HOST=0.0.0.0 python rodar.py
APP_DEBUG=false python rodar.py
OPEN_BROWSER=false python rodar.py
```

Para apresentação no próprio computador, prefira deixar o padrão e acessar `localhost`.
