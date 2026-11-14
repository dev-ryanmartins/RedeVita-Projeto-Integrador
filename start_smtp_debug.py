#!/usr/bin/env python3
"""
Script para iniciar o servidor SMTP de depuração local (modo offline).

Use este script para testar envios de e-mail sem credenciais reais e sem
internet, exibindo todas as mensagens recebidas diretamente no console.

Como usar:
    python start_smtp_debug.py

O servidor roda em localhost:1025.

NOTA DE COMPATIBILIDADE:
As versões anteriores usavam os módulos `smtpd` e `asyncore`, que foram
REMOVIDOS da biblioteca padrão do Python na versão 3.12 (PEP 594). Esta versão
implementa o servidor com `asyncio` (biblioteca padrão), funcionando em Python
3.12+ sem dependências externas — ideal para a apresentação em ambiente offline.
"""

import asyncio
import sys
from email.parser import Parser

HOST = "localhost"
PORT = 1025


def _print_message(peer, mail_from: str, rcpt_to: list, raw_data: bytes) -> None:
    """Formata e imprime uma mensagem de e-mail recebida no console."""
    print("\n" + "=" * 80)
    print("📧 NOVO E-MAIL RECEBIDO")
    print("=" * 80)
    print(f"De: {mail_from}")
    print(f"Para: {', '.join(rcpt_to)}")
    print(f"Cliente: {peer}")
    print("-" * 80)

    parser = Parser()
    message = parser.parsestr(raw_data.decode("utf-8", errors="ignore"))

    print(f"Assunto: {message.get('Subject', '(sem assunto)')}")
    print(f"Data: {message.get('Date', '(sem data)')}")
    print("-" * 80)
    print("Corpo do e-mail:")
    print("-" * 80)

    body = message.get_payload()
    if isinstance(body, list):
        for part in body:
            content_type = part.get_content_type()
            if content_type in ("text/plain", "text/html"):
                payload = part.get_payload(decode=True)
                if payload:
                    print(payload.decode("utf-8", errors="ignore"))
    else:
        print(body)

    print("=" * 80 + "\n")


async def _handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    """Processa uma conexão SMTP de depuração (sink local)."""
    peer = writer.get_extra_info("peername")
    mail_from = ""
    rcpt_to = []
    data_mode = False
    data_lines = []

    async def enviar(linha: str) -> None:
        writer.write((linha + "\r\n").encode("utf-8"))
        await writer.drain()

    await enviar("220 RedeVita SMTP Debug server - pronto")

    try:
        while True:
            line = await reader.readline()
            if not line:
                break

            if data_mode:
                if line.strip() == b".":
                    data_mode = False
                    _print_message(peer, mail_from, rcpt_to, b"".join(data_lines))
                    await enviar("250 OK: mensagem aceita")
                    mail_from = ""
                    rcpt_to = []
                    data_lines = []
                else:
                    data_lines.append(line)
                continue

            comando = line.strip()
            upper = comando.upper()

            if upper.startswith(b"EHLO") or upper.startswith(b"HELO"):
                await enviar("250-RedeVita SMTP Debug")
                await enviar("250 AUTH LOGIN PLAIN")
            elif upper.startswith(b"MAIL FROM"):
                mail_from = comando[10:].strip().strip(b"<>").decode("utf-8", "ignore")
                await enviar("250 OK")
            elif upper.startswith(b"RCPT TO"):
                rcpt_to.append(comando[8:].strip().strip(b"<>").decode("utf-8", "ignore"))
                await enviar("250 OK")
            elif upper.startswith(b"DATA"):
                data_mode = True
                await enviar("354 End data with <CR><LF>.<CR><LF>")
            elif upper.startswith(b"RSET"):
                mail_from, rcpt_to, data_mode, data_lines = "", [], False, []
                await enviar("250 OK")
            elif upper.startswith(b"AUTH"):
                # Aceita qualquer credencial: servidor de depuração local.
                await enviar("334 VXNlcm5hbWU6")  # base64 de "Username:"
                usuario = await reader.readline()
                await enviar("334 UGFzc3dvcmQ6")  # base64 de "Password:"
                await reader.readline()
                await enviar("235 Authentication successful")
            elif upper.startswith(b"NOOP"):
                await enviar("250 OK")
            elif upper.startswith(b"STARTTLS"):
                await enviar("454 TLS not available on debug server")
            elif upper.startswith(b"QUIT"):
                await enviar("221 Bye")
                break
            else:
                await enviar("250 OK")
    except (ConnectionResetError, BrokenPipeError):
        pass
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass


async def _serve() -> None:
    servidor = await asyncio.start_server(_handle_client, HOST, PORT)
    enderecos = ", ".join(str(sock.getsockname()) for sock in servidor.sockets)
    print("=" * 80)
    print("🚀 Servidor SMTP de Depuração do RedeVita")
    print("=" * 80)
    print(f"📍 Host: {HOST}")
    print(f"🔌 Porta: {PORT}")
    print(f"📡 Servidor ativo em: {enderecos}")
    print("=" * 80)
    print("\n💡 Os e-mails enviados pelo Flask serão exibidos aqui no console")
    print("💡 Pressione Ctrl+C para parar o servidor\n")
    print("=" * 80 + "\n")

    async with servidor:
        await servidor.serve_forever()


def main() -> None:
    """Inicia o servidor SMTP de depuração."""
    try:
        asyncio.run(_serve())
    except KeyboardInterrupt:
        print("\n\n⏹️  Servidor SMTP interrompido pelo usuário")
        print("👋 Até logo!")
        sys.exit(0)
    except OSError as e:
        print(f"\n❌ Não foi possível iniciar o servidor SMTP: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
