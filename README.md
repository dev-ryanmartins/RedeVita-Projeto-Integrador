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
