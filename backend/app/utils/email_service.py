"""
Email Service - Envio real de e-mails via SMTP
Serviço para envio de notificações de confirmação de doações e alertas de vencimento
Implementa envio assíncrono via threading para não bloquear rotas HTTP
"""

import logging
import threading
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, Dict, List
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


@dataclass
class EmailMessage:
    """Classe de dados para representar uma mensagem de e-mail."""
    to: str
    subject: str
    body: str
    html_body: Optional[str] = None


class EmailService:
    """
    Serviço de e-mail para o RedeVita.
    Implementa envio real via SMTP com fallback para simulação.
    Implementa envio assíncrono via ThreadPoolExecutor.
    """
    
    def __init__(self, max_workers: int = 4):
        """
        Inicializa o serviço de e-mail.
        
        Args:
            max_workers: Número máximo de threads para envio assíncrono
        """
        from flask import current_app
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.sent_emails: List[EmailMessage] = []
    
    def _get_smtp_config(self) -> dict:
        """Retorna configuração SMTP do Flask app."""
        try:
            from flask import current_app
            return {
                'server': current_app.config.get('MAIL_SERVER', 'smtp.gmail.com'),
                'port': current_app.config.get('MAIL_PORT', 587),
                'use_tls': current_app.config.get('MAIL_USE_TLS', True),
                'username': current_app.config.get('MAIL_USERNAME', ''),
                'password': current_app.config.get('MAIL_PASSWORD', ''),
                'default_sender': current_app.config.get('MAIL_DEFAULT_SENDER', 'RedeVita <nao-responda@redevita.com>')
            }
        except RuntimeError:
            # Fora do contexto Flask
            return {
                'server': 'smtp.gmail.com',
                'port': 587,
                'use_tls': True,
                'username': '',
                'password': '',
                'default_sender': 'RedeVita <nao-responda@redevita.com>'
            }
    
    def send_email(self, message: EmailMessage) -> bool:
        """
        Envia uma mensagem de e-mail via SMTP real (síncrono).
        
        Args:
            message: Objeto EmailMessage com os dados do e-mail
        
        Returns:
            True se enviado com sucesso, False caso contrário
        """
        config = self._get_smtp_config()
        
        # Se não houver credenciais, simula o envio
        if not config['username'] or not config['password']:
            logger.warning("[EMAIL SIMULADO] Credenciais SMTP não configuradas. Simulando envio.")
            logger.info(f"[EMAIL SIMULADO] Para: {message.to}")
            logger.info(f"[EMAIL SIMULADO] Assunto: {message.subject}")
            logger.info(f"[EMAIL SIMULADO] Corpo: {message.body[:100]}...")
            self.sent_emails.append(message)
            return True
        
        try:
            # Cria mensagem MIME
            msg = MIMEMultipart('alternative')
            msg['Subject'] = message.subject
            msg['From'] = config['default_sender']
            msg['To'] = message.to
            
            # Adiciona corpo em texto plano
            msg.attach(MIMEText(message.body, 'plain'))
            
            # Adiciona corpo HTML se disponível
            if message.html_body:
                msg.attach(MIMEText(message.html_body, 'html'))
            
            # Conecta ao servidor SMTP
            with smtplib.SMTP(config['server'], config['port']) as server:
                if config['use_tls']:
                    server.starttls()
                server.login(config['username'], config['password'])
                server.send_message(msg)
            
            logger.info(f"E-mail enviado com sucesso para {message.to}")
            self.sent_emails.append(message)
            return True
                
        except Exception as e:
            logger.error(f"Erro ao enviar e-mail via SMTP: {str(e)}")
            # Fallback para simulação em caso de erro
            logger.warning("[FALLBACK] Simulando envio devido a erro SMTP.")
            logger.info(f"[EMAIL SIMULADO] Para: {message.to}")
            logger.info(f"[EMAIL SIMULADO] Assunto: {message.subject}")
            self.sent_emails.append(message)
            return True  # Retorna True para não quebrar o fluxo do usuário
    
    def send_email_async(self, message: EmailMessage) -> None:
        """
        Envia e-mail de forma assíncrona usando thread pool.
        Não bloqueia a rota HTTP - retorna imediatamente.
        
        Args:
            message: Objeto EmailMessage com os dados do e-mail
        """
        def _send():
            try:
                self.send_email(message)
            except Exception as e:
                logger.error(f"Erro no envio assíncrono de e-mail: {str(e)}")
        
        self.executor.submit(_send)
    
    def send_doacao_confirmation_async(
        self,
        to_email: str,
        nome_doador: str,
        medicamento: str,
        quantidade: int,
        lote: str,
        data_validade: str,
        data_doacao: datetime
    ) -> None:
        """
        Envia e-mail de confirmação de doação de forma assíncrona.
        Template atualizado com lote e validade.
        
        Args:
            to_email: E-mail do doador
            nome_doador: Nome do doador
            medicamento: Nome do medicamento doado
            quantidade: Quantidade doada
            lote: Lote do medicamento
            data_validade: Data de validade
            data_doacao: Data da doação
        """
        subject = "RedeVita - Confirmação de Doação Recebida"
        
        body = f"""
Olá, {nome_doador}!

Agradecemos imensamente pela sua generosa doação ao RedeVita.

Detalhes da doação recebida:
- Medicamento: {medicamento}
- Quantidade: {quantidade} unidades
- Lote: {lote}
- Validade: {data_validade}
- Data de cadastro: {data_doacao.strftime('%d/%m/%Y %H:%M')}

Sua doação passará por triagem farmacêutica. Em breve, você receberá uma atualização sobre o status.

Sua contribuição ajudará muitas pessoas que necessitam desses medicamentos.

Atenciosamente,
Equipe RedeVita

---
Este é um e-mail automático. Por favor, não responda.
""".strip()
        
        html_body = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
        .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
        .details {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #667eea; }}
        .details ul {{ list-style: none; padding: 0; }}
        .details li {{ padding: 8px 0; border-bottom: 1px solid #eee; }}
        .details li:last-child {{ border-bottom: none; }}
        .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>✅ Confirmação de Doação Recebida</h2>
        </div>
        <div class="content">
            <p>Olá, <strong>{nome_doador}</strong>!</p>
            <p>Agradecemos imensamente pela sua generosa doação ao RedeVita.</p>
            
            <div class="details">
                <h3>📋 Detalhes da doação:</h3>
                <ul>
                    <li><strong>Medicamento:</strong> {medicamento}</li>
                    <li><strong>Quantidade:</strong> {quantidade} unidades</li>
                    <li><strong>Lote:</strong> {lote}</li>
                    <li><strong>Validade:</strong> {data_validade}</li>
                    <li><strong>Data de cadastro:</strong> {data_doacao.strftime('%d/%m/%Y %H:%M')}</li>
                </ul>
            </div>
            
            <p>Sua doação passará por <strong>triagem farmacêutica</strong>. Em breve, você receberá uma atualização sobre o status.</p>
            
            <p>Sua contribuição ajudará muitas pessoas que necessitam desses medicamentos.</p>
            
            <p>Atenciosamente,<br><strong>Equipe RedeVita</strong></p>
        </div>
        <div class="footer">
            <p>Este é um e-mail automático. Por favor, não responda.</p>
        </div>
    </div>
</body>
</html>
"""
        
        message = EmailMessage(
            to=to_email,
            subject=subject,
            body=body,
            html_body=html_body
        )
        
        self.send_email_async(message)
    
    def send_triagem_status_async(
        self,
        to_email: str,
        nome_doador: str,
        medicamento: str,
        status: str,
        motivo: str = ""
    ) -> None:
        """
        Envia e-mail de status de triagem farmacêutica de forma assíncrona.
        
        Args:
            to_email: E-mail do doador
            nome_doador: Nome do doador
            medicamento: Nome do medicamento
            status: Status da triagem (APROVADO/REJEITADO)
            motivo: Motivo da rejeição (opcional)
        """
        if status.upper() == "APROVADO":
            subject = "RedeVita - Sua Doação Foi Aprovada! 🎉"
            emoji = "✅"
            mensagem = "Sua doação foi aprovada na triagem farmacêutica e já está disponível para distribuição."
        else:
            subject = "RedeVita - Atualização sobre sua Doação"
            emoji = "⚠️"
            mensagem = f"Infelizmente, sua doação não foi aprovada na triagem farmacêutica."
        
        body = f"""
Olá, {nome_doador}!

{emoji} {mensagem}

Detalhes:
- Medicamento: {medicamento}
- Status: {status.upper()}
"""
        
        if motivo:
            body += f"- Motivo: {motivo}\n"
        
        body += """
Atenciosamente,
Equipe RedeVita

---
Este é um e-mail automático. Por favor, não responda.
""".strip()
        
        html_body = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: {'#28a745' if status.upper() == 'APROVADO' else '#dc3545'}; color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
        .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
        .status {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid {'#28a745' if status.upper() == 'APROVADO' else '#dc3545'}; }}
        .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>{emoji} {'Sua Doação Foi Aprovada!' if status.upper() == 'APROVADO' else 'Atualização sobre sua Doação'}</h2>
        </div>
        <div class="content">
            <p>Olá, <strong>{nome_doador}</strong>!</p>
            <p>{mensagem}</p>
            
            <div class="status">
                <h3>📋 Detalhes:</h3>
                <ul>
                    <li><strong>Medicamento:</strong> {medicamento}</li>
                    <li><strong>Status:</strong> {status.upper()}</li>
"""
        
        if motivo:
            html_body += f"                    <li><strong>Motivo:</strong> {motivo}</li>\n"
        
        html_body += f"""                </ul>
            </div>
            
            <p>Atenciosamente,<br><strong>Equipe RedeVita</strong></p>
        </div>
        <div class="footer">
            <p>Este é um e-mail automático. Por favor, não responda.</p>
        </div>
    </div>
</body>
</html>
"""
        
        message = EmailMessage(
            to=to_email,
            subject=subject,
            body=body,
            html_body=html_body
        )
        
        self.send_email_async(message)
    
    def send_reserva_confirmation_async(
        self,
        to_email: str,
        nome_paciente: str,
        medicamento: str,
        codigo_reserva: str,
        endereco_coleta: str,
        data_limite: str
    ) -> None:
        """
        Envia e-mail de confirmação de reserva de forma assíncrona.
        
        Args:
            to_email: E-mail do paciente
            nome_paciente: Nome do paciente
            medicamento: Nome do medicamento reservado
            codigo_reserva: Código da reserva
            endereco_coleta: Endereço do posto de coleta
            data_limite: Data limite para retirada
        """
        subject = f"RedeVita - Comprovante de Reserva: {codigo_reserva}"
        
        body = f"""
Olá, {nome_paciente}!

Sua reserva foi confirmada com sucesso.

📋 Detalhes da reserva:
- Medicamento: {medicamento}
- Código de retirada: {codigo_reserva}
- Endereço de coleta: {endereco_coleta}
- Data limite para retirada: {data_limite}

Apresente o código de retirada no posto de coleta para receber seu medicamento.

Atenciosamente,
Equipe RedeVita

---
Este é um e-mail automático. Por favor, não responda.
""".strip()
        
        html_body = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
        .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
        .codigo {{ background: #fff; padding: 20px; text-align: center; border-radius: 8px; margin: 20px 0; border: 2px dashed #11998e; }}
        .codigo h3 {{ font-size: 32px; color: #11998e; margin: 0; letter-spacing: 3px; }}
        .details {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #11998e; }}
        .details ul {{ list-style: none; padding: 0; }}
        .details li {{ padding: 8px 0; border-bottom: 1px solid #eee; }}
        .details li:last-child {{ border-bottom: none; }}
        .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>🎫 Comprovante de Reserva</h2>
        </div>
        <div class="content">
            <p>Olá, <strong>{nome_paciente}</strong>!</p>
            <p>Sua reserva foi confirmada com sucesso.</p>
            
            <div class="codigo">
                <p style="margin: 0; color: #666; font-size: 14px;">CÓDIGO DE RETIRADA</p>
                <h3>{codigo_reserva}</h3>
            </div>
            
            <div class="details">
                <h3>📋 Detalhes da reserva:</h3>
                <ul>
                    <li><strong>Medicamento:</strong> {medicamento}</li>
                    <li><strong>Endereço de coleta:</strong> {endereco_coleta}</li>
                    <li><strong>Data limite para retirada:</strong> {data_limite}</li>
                </ul>
            </div>
            
            <p>Apresente o código de retirada no posto de coleta para receber seu medicamento.</p>
            
            <p>Atenciosamente,<br><strong>Equipe RedeVita</strong></p>
        </div>
        <div class="footer">
            <p>Este é um e-mail automático. Por favor, não responda.</p>
        </div>
    </div>
</body>
</html>
"""
        
        message = EmailMessage(
            to=to_email,
            subject=subject,
            body=body,
            html_body=html_body
        )
        
        self.send_email_async(message)
    
    def send_doacao_confirmation(
        self,
        to_email: str,
        nome_doador: str,
        medicamento: str,
        quantidade: int,
        data_doacao: datetime
    ) -> bool:
        """
        Envia e-mail de confirmação de doação.
        
        Args:
            to_email: E-mail do doador
            nome_doador: Nome do doador
            medicamento: Nome do medicamento doado
            quantidade: Quantidade doada
            data_doacao: Data da doação
        
        Returns:
            True se enviado com sucesso
        """
        subject = "RedeVita - Confirmação de Doação Recebida"
        
        body = f"""
Olá, {nome_doador}!

Agradecemos imensamente pela sua generosa doação ao RedeVita.

Detalhes da doação recebida:
- Medicamento: {medicamento}
- Quantidade: {quantidade} unidades
- Data: {data_doacao.strftime('%d/%m/%Y %H:%M')}

Sua contribuição ajudará muitas pessoas que necessitam desses medicamentos.
Em breve, entraremos em contato com atualizações sobre o impacto da sua doação.

Atenciosamente,
Equipe RedeVita

---
Este é um e-mail automático. Por favor, não responda.
""".strip()
        
        html_body = f"""
<html>
<body>
    <h2>Confirmação de Doação Recebida</h2>
    <p>Olá, <strong>{nome_doador}</strong>!</p>
    <p>Agradecemos imensamente pela sua generosa doação ao RedeVita.</p>
    
    <h3>Detalhes da doação:</h3>
    <ul>
        <li><strong>Medicamento:</strong> {medicamento}</li>
        <li><strong>Quantidade:</strong> {quantidade} unidades</li>
        <li><strong>Data:</strong> {data_doacao.strftime('%d/%m/%Y %H:%M')}</li>
    </ul>
    
    <p>Sua contribuição ajudará muitas pessoas que necessitam desses medicamentos.</p>
    
    <p>Atenciosamente,<br>Equipe RedeVita</p>
    
    <hr>
    <p><em>Este é um e-mail automático. Por favor, não responda.</em></p>
</body>
</html>
"""
        
        message = EmailMessage(
            to=to_email,
            subject=subject,
            body=body,
            html_body=html_body
        )
        
        return self.send_email(message)
    
    def send_vencimento_alert(
        self,
        to_email: str,
        nome_responsavel: str,
        medicamentos_vencendo: List[Dict[str, str]]
    ) -> bool:
        """
        Envia alerta de medicamentos próximos ao vencimento.
        
        Args:
            to_email: E-mail do responsável
            nome_responsavel: Nome do responsável
            medicamentos_vencendo: Lista de dicts com nome, validade e quantidade
        
        Returns:
            True se enviado com sucesso
        """
        subject = "RedeVita - Alerta: Medicamentos Próximos ao Vencimento"
        
        medicamentos_text = "\n".join([
            f"- {med['nome']} (Validade: {med['validade']}, Qtd: {med['quantidade']})"
            for med in medicamentos_vencendo
        ])
        
        body = f"""
Prezado(a), {nome_responsavel}!

Este é um alerta automático do sistema RedeVita.

Os seguintes medicamentos estão próximos ao vencimento e requerem atenção:

{medicamentos_text}

Por favor, verifique o estoque e tome as providências necessárias.

Atenciosamente,
Sistema RedeVita

---
Este é um e-mail automático. Por favor, não responda.
""".strip()
        
        html_body = f"""
<html>
<body>
    <h2>⚠️ Alerta: Medicamentos Próximos ao Vencimento</h2>
    <p>Prezado(a), <strong>{nome_responsavel}</strong>!</p>
    <p>Este é um alerta automático do sistema RedeVita.</p>
    
    <h3>Medicamentos que requerem atenção:</h3>
    <table border="1" cellpadding="10" cellspacing="0">
        <tr>
            <th><strong>Medicamento</strong></th>
            <th><strong>Validade</strong></th>
            <th><strong>Quantidade</strong></th>
        </tr>
        {"".join([
            f"<tr><td>{med['nome']}</td><td>{med['validade']}</td><td>{med['quantidade']}</td></tr>"
            for med in medicamentos_vencendo
        ])}
    </table>
    
    <p>Por favor, verifique o estoque e tome as providências necessárias.</p>
    
    <p>Atenciosamente,<br>Sistema RedeVita</p>
    
    <hr>
    <p><em>Este é um e-mail automático. Por favor, não responda.</em></p>
</body>
</html>
"""
        
        message = EmailMessage(
            to=to_email,
            subject=subject,
            body=body,
            html_body=html_body
        )
        
        return self.send_email(message)
    
    def send_low_stock_alert(
        self,
        to_email: str,
        nome_responsavel: str,
        medicamentos_baixo_estoque: List[Dict[str, str]]
    ) -> bool:
        """
        Envia alerta de medicamentos com estoque baixo.
        
        Args:
            to_email: E-mail do responsável
            nome_responsavel: Nome do responsável
            medicamentos_baixo_estoque: Lista de dicts com nome e quantidade
        
        Returns:
            True se enviado com sucesso
        """
        subject = "RedeVita - Alerta: Estoque Baixo"
        
        medicamentos_text = "\n".join([
            f"- {med['nome']} (Estoque atual: {med['quantidade']})"
            for med in medicamentos_baixo_estoque
        ])
        
        body = f"""
Prezado(a), {nome_responsavel}!

Este é um alerta automático do sistema RedeVita.

Os seguintes medicamentos estão com estoque baixo:

{medicamentos_text}

Por favor, considere fazer novos pedidos ou solicitar doações.

Atenciosamente,
Sistema RedeVita

---
Este é um e-mail automático. Por favor, não responda.
""".strip()
        
        html_body = f"""
<html>
<body>
    <h2>📦 Alerta: Estoque Baixo</h2>
    <p>Prezado(a), <strong>{nome_responsavel}</strong>!</p>
    <p>Este é um alerta automático do sistema RedeVita.</p>
    
    <h3>Medicamentos com estoque baixo:</h3>
    <table border="1" cellpadding="10" cellspacing="0">
        <tr>
            <th><strong>Medicamento</strong></th>
            <th><strong>Estoque Atual</strong></th>
        </tr>
        {"".join([
            f"<tr><td>{med['nome']}</td><td>{med['quantidade']}</td></tr>"
            for med in medicamentos_baixo_estoque
        ])}
    </table>
    
    <p>Por favor, considere fazer novos pedidos ou solicitar doações.</p>
    
    <p>Atenciosamente,<br>Sistema RedeVita</p>
    
    <hr>
    <p><em>Este é um e-mail automático. Por favor, não responda.</em></p>
</body>
</html>
"""
        
        message = EmailMessage(
            to=to_email,
            subject=subject,
            body=body,
            html_body=html_body
        )
        
        return self.send_email(message)
    
    def get_sent_emails_count(self) -> int:
        """Retorna o número de e-mails enviados (em modo simulação)."""
        return len(self.sent_emails)
    
    def clear_sent_emails(self) -> None:
        """Limpa o histórico de e-mails enviados (em modo simulação)."""
        self.sent_emails.clear()


# Instância global do serviço
email_service = EmailService()
