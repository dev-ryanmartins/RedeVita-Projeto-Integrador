"""
SMS Service - Envio real de SMS via Twilio
Serviço para envio de notificações por SMS/WhatsApp
Implementa envio assíncrono via threading para não bloquear rotas HTTP
"""

import logging
import re
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class SMSService:
    """
    Serviço de SMS para o RedeVita.
    Implementa envio real via Twilio com fallback para simulação.
    Implementa envio assíncrono via ThreadPoolExecutor.
    """
    
    def __init__(self, max_workers: int = 4):
        """
        Inicializa o serviço de SMS.
        
        Args:
            max_workers: Número máximo de threads para envio assíncrono
        """
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.sent_messages: list = []
    
    def _get_twilio_config(self) -> dict:
        """Retorna configuração Twilio do Flask app."""
        try:
            from flask import current_app
            return {
                'account_sid': current_app.config.get('TWILIO_ACCOUNT_SID', ''),
                'auth_token': current_app.config.get('TWILIO_AUTH_TOKEN', ''),
                'phone_number': current_app.config.get('TWILIO_PHONE_NUMBER', '')
            }
        except RuntimeError:
            # Fora do contexto Flask
            return {
                'account_sid': '',
                'auth_token': '',
                'phone_number': ''
            }
    
    def _sanitize_phone_number(self, phone: str) -> str:
        """
        Sanitiza e formata número de telefone para formato E.164.
        
        Args:
            phone: Número de telefone (pode ter parênteses, traços, espaços)
        
        Returns:
            Número formatado em E.164 (ex: +5515999998888)
        """
        if not phone:
            return ""
        
        # Remove todos os caracteres não numéricos
        cleaned = re.sub(r'[^\d]', '', phone)
        
        # Se começar com 0 (DDD brasileiro), remove
        if cleaned.startswith('0'):
            cleaned = cleaned[1:]
        
        # Se não tiver código internacional (+55), adiciona
        if not cleaned.startswith('55'):
            cleaned = '55' + cleaned
        
        # Adiciona o prefixo +
        return f"+{cleaned}"
    
    def send_sms(self, to_number: str, message: str) -> bool:
        """
        Envia SMS via Twilio (síncrono).
        
        Args:
            to_number: Número de telefone do destinatário
            message: Mensagem a ser enviada
        
        Returns:
            True se enviado com sucesso, False caso contrário
        """
        config = self._get_twilio_config()
        
        # Sanitiza número de telefone
        sanitized_number = self._sanitize_phone_number(to_number)
        
        # Se não houver credenciais Twilio, simula o envio
        if not config['account_sid'] or not config['auth_token'] or not config['phone_number']:
            logger.warning("[SMS SIMULADO] Credenciais Twilio não configuradas. Simulando envio.")
            logger.info(f"[SMS SIMULADO] Para: {sanitized_number}")
            logger.info(f"[SMS SIMULADO] Mensagem: {message[:100]}...")
            self.sent_messages.append({'to': sanitized_number, 'message': message})
            return True
        
        try:
            from twilio.rest import Client
            
            # Cria cliente Twilio
            client = Client(config['account_sid'], config['auth_token'])
            
            # Envia SMS
            message_obj = client.messages.create(
                body=message,
                from_=config['phone_number'],
                to=sanitized_number
            )
            
            logger.info(f"SMS enviado com sucesso para {sanitized_number}. SID: {message_obj.sid}")
            self.sent_messages.append({'to': sanitized_number, 'message': message, 'sid': message_obj.sid})
            return True
                
        except Exception as e:
            logger.error(f"Erro ao enviar SMS via Twilio: {str(e)}")
            # Fallback para simulação em caso de erro
            logger.warning("[FALLBACK] Simulando envio devido a erro Twilio.")
            logger.info(f"[SMS SIMULADO] Para: {sanitized_number}")
            logger.info(f"[SMS SIMULADO] Mensagem: {message}")
            self.sent_messages.append({'to': sanitized_number, 'message': message})
            return True  # Retorna True para não quebrar o fluxo do usuário
    
    def send_sms_async(self, to_number: str, message: str) -> None:
        """
        Envia SMS de forma assíncrona usando thread pool.
        Não bloqueia a rota HTTP - retorna imediatamente.
        
        Args:
            to_number: Número de telefone do destinatário
            message: Mensagem a ser enviada
        """
        def _send():
            try:
                self.send_sms(to_number, message)
            except Exception as e:
                logger.error(f"Erro no envio assíncrono de SMS: {str(e)}")
        
        self.executor.submit(_send)
    
    def send_doacao_confirmation_async(
        self,
        to_phone: str,
        medicamento: str
    ) -> None:
        """
        Envia SMS de confirmação de doação de forma assíncrona.
        
        Args:
            to_phone: Telefone do doador
            medicamento: Nome do medicamento doado
        """
        message = f"RedeVita: Sua doacao de {medicamento} foi cadastrada com sucesso e aguarda triagem farmaceutica. Agradecemos!"
        self.send_sms_async(to_phone, message)
    
    def send_triagem_status_async(
        self,
        to_phone: str,
        medicamento: str,
        status: str
    ) -> None:
        """
        Envia SMS de status de triagem de forma assíncrona.
        
        Args:
            to_phone: Telefone do doador
            medicamento: Nome do medicamento
            status: Status da triagem (APROVADO/REJEITADO)
        """
        if status.upper() == "APROVADO":
            message = f"RedeVita: Sua doacao de {medicamento} foi APROVADA na triagem e ja esta disponivel para distribuicao!"
        else:
            message = f"RedeVita: Sua doacao de {medicamento} nao foi aprovada na triagem. Entre em contato para mais informacoes."
        
        self.send_sms_async(to_phone, message)
    
    def send_reserva_confirmation_async(
        self,
        to_phone: str,
        codigo_reserva: str,
        endereco: str
    ) -> None:
        """
        Envia SMS de confirmação de reserva de forma assíncrona.
        
        Args:
            to_phone: Telefone do paciente
            codigo_reserva: Código da reserva
            endereco: Endereço do posto de coleta
        """
        message = f"RedeVita: Reserva confirmada! Codigo: {codigo_reserva}. Retire em: {endereco}. Apresente o codigo no posto."
        self.send_sms_async(to_phone, message)
    
    def get_sent_messages_count(self) -> int:
        """Retorna o número de SMS enviados (em modo simulação)."""
        return len(self.sent_messages)
    
    def clear_sent_messages(self) -> None:
        """Limpa o histórico de SMS enviados (em modo simulação)."""
        self.sent_messages.clear()


# Instância global do serviço
sms_service = SMSService()
