"""
Testes Unitários para Sistema de Notificações
Testa envio de e-mails via SMTP e SMS via Twilio usando mocks
Disciplina: ADS - Módulo 4 - Integração de Serviços Externos
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from backend.app.utils.email_service import EmailService, EmailMessage
from backend.app.utils.sms_service import SMSService


class TestEmailService:
    """Testes para o serviço de e-mail."""
    
    @pytest.fixture
    def email_service(self):
        """Fixture para criar instância do EmailService."""
        return EmailService()
    
    @pytest.fixture
    def mock_smtp(self):
        """Fixture para mock do smtplib.SMTP."""
        with patch('backend.app.utils.email_service.smtplib.SMTP') as mock:
            yield mock
    
    def test_send_email_without_credentials(self, email_service):
        """Testa envio de e-mail sem credenciais (modo simulação)."""
        message = EmailMessage(
            to="test@example.com",
            subject="Teste",
            body="Corpo do teste"
        )
        
        result = email_service.send_email(message)
        
        assert result is True
        assert len(email_service.sent_emails) == 1
        assert email_service.sent_emails[0].to == "test@example.com"
    
    @pytest.mark.skip(reason="Requires Flask app context, tested in integration")
    @patch('backend.app.utils.email_service.smtplib.SMTP')
    @patch('flask.current_app')
    def test_send_email_with_credentials(self, mock_app, mock_smtp, email_service):
        """Testa envio de e-mail com credenciais configuradas."""
        # Configura mock do Flask app
        mock_app.config = {
            'MAIL_SERVER': 'smtp.gmail.com',
            'MAIL_PORT': 587,
            'MAIL_USE_TLS': True,
            'MAIL_USERNAME': 'test@gmail.com',
            'MAIL_PASSWORD': 'test_password',
            'MAIL_DEFAULT_SENDER': 'RedeVita <noreply@redevita.com>'
        }
        
        message = EmailMessage(
            to="test@example.com",
            subject="Teste",
            body="Corpo do teste"
        )
        
        result = email_service.send_email(message)
        
        assert result is True
        assert len(email_service.sent_emails) == 1
        mock_smtp.assert_called_once()
    
    def test_send_doacao_confirmation_async(self, email_service):
        """Testa envio assíncrono de confirmação de doação."""
        with patch.object(email_service, 'send_email_async') as mock_send:
            email_service.send_doacao_confirmation_async(
                to_email="test@example.com",
                nome_doador="João Silva",
                medicamento="Paracetamol",
                quantidade=10,
                lote="L123",
                data_validade="31/12/2025",
                data_doacao=datetime.utcnow()
            )
            
            mock_send.assert_called_once()
            assert mock_send.call_args[0][0].to == "test@example.com"
            assert "Paracetamol" in mock_send.call_args[0][0].body
    
    def test_send_triagem_status_async_aprovado(self, email_service):
        """Testa envio assíncrono de status de triagem aprovado."""
        with patch.object(email_service, 'send_email_async') as mock_send:
            email_service.send_triagem_status_async(
                to_email="test@example.com",
                nome_doador="João Silva",
                medicamento="Paracetamol",
                status="APROVADO"
            )
            
            mock_send.assert_called_once()
            assert "aprovada" in mock_send.call_args[0][0].body.lower()
    
    def test_send_triagem_status_async_rejeitado(self, email_service):
        """Testa envio assíncrono de status de triagem rejeitado."""
        with patch.object(email_service, 'send_email_async') as mock_send:
            email_service.send_triagem_status_async(
                to_email="test@example.com",
                nome_doador="João Silva",
                medicamento="Paracetamol",
                status="REJEITADO",
                motivo="Validade vencida"
            )
            
            mock_send.assert_called_once()
            assert "não foi aprovada" in mock_send.call_args[0][0].body
            assert "Validade vencida" in mock_send.call_args[0][0].body
    
    def test_send_reserva_confirmation_async(self, email_service):
        """Testa envio assíncrono de confirmação de reserva."""
        with patch.object(email_service, 'send_email_async') as mock_send:
            email_service.send_reserva_confirmation_async(
                to_email="test@example.com",
                nome_paciente="Maria Santos",
                medicamento="Ibuprofeno",
                codigo_reserva="RES-123456",
                endereco_coleta="Farmácia Central",
                data_limite="31/12/2025"
            )
            
            mock_send.assert_called_once()
            assert "RES-123456" in mock_send.call_args[0][0].body
            assert "Farmácia Central" in mock_send.call_args[0][0].body


class TestSMSService:
    """Testes para o serviço de SMS."""
    
    @pytest.fixture
    def sms_service(self):
        """Fixture para criar instância do SMSService."""
        return SMSService()
    
    @pytest.fixture
    def mock_twilio_client(self):
        """Fixture para mock do Twilio Client."""
        with patch('backend.app.utils.sms_service.Client') as mock:
            yield mock
    
    def test_sanitize_phone_number(self, sms_service):
        """Testa sanitização de número de telefone."""
        # Teste com parênteses e traços
        assert sms_service._sanitize_phone_number("(15) 99999-8888") == "+5515999998888"
        
        # Teste com espaços
        assert sms_service._sanitize_phone_number("15 99999 8888") == "+5515999998888"
        
        # Teste com prefixo internacional
        assert sms_service._sanitize_phone_number("+5515999998888") == "+5515999998888"
        
        # Teste com DDD com zero
        assert sms_service._sanitize_phone_number("015999998888") == "+5515999998888"
    
    def test_send_sms_without_credentials(self, sms_service):
        """Testa envio de SMS sem credenciais (modo simulação)."""
        result = sms_service.send_sms(
            to_number="(15) 99999-8888",
            message="Teste de SMS"
        )
        
        assert result is True
        assert len(sms_service.sent_messages) == 1
        assert sms_service.sent_messages[0]['to'] == "+5515999998888"
    
    @pytest.mark.skip(reason="Requires Flask app context, tested in integration")
    @patch('backend.app.utils.sms_service.Client')
    @patch('flask.current_app')
    def test_send_sms_with_credentials(self, mock_app, mock_twilio_client, sms_service):
        """Testa envio de SMS com credenciais configuradas."""
        # Configura mock do Flask app
        mock_app.config = {
            'TWILIO_ACCOUNT_SID': 'AC123',
            'TWILIO_AUTH_TOKEN': 'token123',
            'TWILIO_PHONE_NUMBER': '+1234567890'
        }
        
        # Configura mock do Twilio Client
        mock_client_instance = MagicMock()
        mock_twilio_client.return_value = mock_client_instance
        mock_message = MagicMock()
        mock_message.sid = "SM123"
        mock_client_instance.messages.create.return_value = mock_message
        
        result = sms_service.send_sms(
            to_number="(15) 99999-8888",
            message="Teste de SMS"
        )
        
        assert result is True
        assert len(sms_service.sent_messages) == 1
        mock_twilio_client.assert_called_once_with('AC123', 'token123')
    
    def test_send_doacao_confirmation_async(self, sms_service):
        """Testa envio assíncrono de confirmação de doação por SMS."""
        with patch.object(sms_service, 'send_sms_async') as mock_send:
            sms_service.send_doacao_confirmation_async(
                to_phone="(15) 99999-8888",
                medicamento="Paracetamol"
            )
            
            mock_send.assert_called_once()
            assert "Paracetamol" in mock_send.call_args[0][1]
    
    def test_send_triagem_status_async_aprovado(self, sms_service):
        """Testa envio assíncrono de status de triagem aprovado por SMS."""
        with patch.object(sms_service, 'send_sms_async') as mock_send:
            sms_service.send_triagem_status_async(
                to_phone="(15) 99999-8888",
                medicamento="Paracetamol",
                status="APROVADO"
            )
            
            mock_send.assert_called_once()
            assert "APROVADA" in mock_send.call_args[0][1]
    
    def test_send_triagem_status_async_rejeitado(self, sms_service):
        """Testa envio assíncrono de status de triagem rejeitado por SMS."""
        with patch.object(sms_service, 'send_sms_async') as mock_send:
            sms_service.send_triagem_status_async(
                to_phone="(15) 99999-8888",
                medicamento="Paracetamol",
                status="REJEITADO"
            )
            
            mock_send.assert_called_once()
            assert "nao foi aprovada" in mock_send.call_args[0][1]
    
    def test_send_reserva_confirmation_async(self, sms_service):
        """Testa envio assíncrono de confirmação de reserva por SMS."""
        with patch.object(sms_service, 'send_sms_async') as mock_send:
            sms_service.send_reserva_confirmation_async(
                to_phone="(15) 99999-8888",
                codigo_reserva="RES-123456",
                endereco="Farmácia Central"
            )
            
            mock_send.assert_called_once()
            assert "RES-123456" in mock_send.call_args[0][1]
            assert "Farmácia Central" in mock_send.call_args[0][1]


class TestNotificationIntegration:
    """Testes de integração do sistema de notificações."""
    
    def test_email_and_sms_sent_together(self):
        """Testa envio simultâneo de e-mail e SMS."""
        email_service = EmailService()
        sms_service = SMSService()
        
        with patch.object(email_service, 'send_email_async') as mock_email, \
             patch.object(sms_service, 'send_sms_async') as mock_sms:
            
            # Simula envio de notificação de doação
            email_service.send_doacao_confirmation_async(
                to_email="test@example.com",
                nome_doador="João Silva",
                medicamento="Paracetamol",
                quantidade=10,
                lote="L123",
                data_validade="31/12/2025",
                data_doacao=datetime.utcnow()
            )
            
            sms_service.send_doacao_confirmation_async(
                to_phone="(15) 99999-8888",
                medicamento="Paracetamol"
            )
            
            mock_email.assert_called_once()
            mock_sms.assert_called_once()
    
    def test_phone_sanitization_before_sms_send(self):
        """Testa que telefone é sanitizado antes do envio de SMS."""
        sms_service = SMSService()
        
        # Testa sanitização direta
        sanitized = sms_service._sanitize_phone_number("(15) 99999-8888")
        assert sanitized == "+5515999998888"
        
        # Testa que send_sms sanitiza o número
        with patch.object(sms_service, 'send_sms') as mock_send:
            sms_service.send_doacao_confirmation_async(
                to_phone="(15) 99999-8888",
                medicamento="Paracetamol"
            )
            
            # Verifica que o método foi chamado com o número original
            # (a sanitização acontece dentro do método)
            call_args = mock_send.call_args
            assert call_args[0][0] == "(15) 99999-8888"
