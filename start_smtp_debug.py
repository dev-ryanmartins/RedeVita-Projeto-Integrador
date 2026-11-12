#!/usr/bin/env python3
"""
Script para iniciar o servidor SMTP de depuração local.
Use este script para testar envios de e-mail sem credenciais reais.

Como usar:
    python start_smtp_debug.py

O servidor irá rodar em localhost:1025 e imprimirá todos os e-mails
enviados pelo Flask no console, sem precisar de um servidor SMTP real.
"""

import smtpd
import asyncore
from email.parser import Parser
import sys

class DebuggingSMTPServer(smtpd.DebuggingServer):
    """Servidor SMTP de depuração personalizado"""
    
    def process_message(self, peer, mailfrom, rcpttos, data, **kwargs):
        """Processa e imprime mensagens de e-mail no console"""
        print("\n" + "="*80)
        print("📧 NOVO E-MAIL RECEBIDO")
        print("="*80)
        print(f"De: {mailfrom}")
        print(f"Para: {', '.join(rcpttos)}")
        print(f"Cliente: {peer}")
        print("-"*80)
        
        # Parse do e-mail para exibir conteúdo formatado
        parser = Parser()
        message = parser.parsestr(data.decode('utf-8', errors='ignore'))
        
        print(f"Assunto: {message.get('Subject', '(sem assunto)')}")
        print(f"Data: {message.get('Date', '(sem data)')}")
        print("-"*80)
        print("Corpo do e-mail:")
        print("-"*80)
        
        # Exibe corpo do e-mail
        body = message.get_payload()
        if isinstance(body, list):
            for part in body:
                content_type = part.get_content_type()
                if content_type == 'text/plain' or content_type == 'text/html':
                    print(part.get_payload(decode=True).decode('utf-8', errors='ignore'))
        else:
            print(body)
        
        print("="*80 + "\n")
        
        # Chama o método original para processamento padrão
        return super().process_message(peer, mailfrom, rcpttos, data, **kwargs)

def main():
    """Inicia o servidor SMTP de depuração"""
    host = 'localhost'
    port = 1025
    
    print("="*80)
    print("🚀 Servidor SMTP de Depuração do RedeVita")
    print("="*80)
    print(f"📍 Host: {host}")
    print(f"🔌 Porta: {port}")
    print(f"📡 Servidor ativo e pronto para receber e-mails")
    print("="*80)
    print("\n💡 Os e-mails enviados pelo Flask serão exibidos aqui no console")
    print("💡 Pressione Ctrl+C para parar o servidor\n")
    print("="*80 + "\n")
    
    try:
        # Cria e inicia o servidor
        server = DebuggingSMTPServer((host, port), None)
        print(f"✅ Servidor SMTP rodando em {host}:{port}")
        print("⏳ Aguardando e-mails...\n")
        
        # Inicia o loop de eventos
        asyncore.loop()
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Servidor SMTP interrompido pelo usuário")
        print("👋 Até logo!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erro ao iniciar servidor SMTP: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
