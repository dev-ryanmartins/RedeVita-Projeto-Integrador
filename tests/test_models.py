"""
Test Models - Suíte de Testes de Modelos
Testa o funcionamento dos modelos do banco de dados
"""

import unittest
import sys
import os
from datetime import date, datetime, timedelta

# Adiciona o diretório backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from main import create_app
from app.database import db
from app.models.usuario import Usuario
from app.models.medicamento import Medicamento
from app.models.medicamento_referencia import MedicamentoReferencia
from app.models.paciente import Paciente
from app.models.medico import Medico
from app.models.farmacia import Farmacia
from app.models.doacao import Doacao
from app.models.log_atividade import LogAtividade


class TestModels(unittest.TestCase):
    """Testa os modelos do banco de dados"""
    
    def setUp(self):
        """Configura a aplicação e o banco de teste"""
        self.app = create_app({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        })
        
        with self.app.app_context():
            db.create_all()
    
    def tearDown(self):
        """Limpa o banco após cada teste"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_usuario_creation(self):
        """Testa a criação de um usuário"""
        with self.app.app_context():
            from app.core.security import criptografar_senha
            
            usuario = Usuario(
                nome='Test User',
                cpf='12345678901',
                email='test@example.com',
                senha=criptografar_senha('password123'),
                cargo='Admin',
                ativo=True
            )
            
            db.session.add(usuario)
            db.session.commit()
            
            # Verifica se foi salvo
            saved_usuario = Usuario.query.filter_by(cpf='12345678901').first()
            self.assertIsNotNone(saved_usuario)
            self.assertEqual(saved_usuario.nome, 'Test User')
            self.assertEqual(saved_usuario.email, 'test@example.com')
            self.assertEqual(saved_usuario.cargo, 'Admin')
            self.assertTrue(saved_usuario.ativo)
    
    def test_medicamento_creation(self):
        """Testa a criação de um medicamento"""
        with self.app.app_context():
            from app.utils.semaforo import calcular_status_semaforo
            
            validade = date.today() + timedelta(days=365)
            status = calcular_status_semaforo(validade)
            
            medicamento = Medicamento(
                nome='Paracetamol 500mg',
                lote='TEST-001',
                data_validade=validade,
                quantidade=100,
                status_semaforo=status,
                tarja='Sem Tarja',
                principio_ativo='Paracetamol',
                uso_continuo=False
            )
            
            db.session.add(medicamento)
            db.session.commit()
            
            # Verifica se foi salvo
            saved_med = Medicamento.query.filter_by(lote='TEST-001').first()
            self.assertIsNotNone(saved_med)
            self.assertEqual(saved_med.nome, 'Paracetamol 500mg')
            self.assertEqual(saved_med.quantidade, 100)
            self.assertEqual(saved_med.tarja, 'Sem Tarja')

    def test_medicamento_portaria_344_referencia_requer_tarja(self):
        """Testa validação automática da Portaria 344 para medicamentos controlados"""
        with self.app.app_context():
            from app.utils.semaforo import calcular_status_semaforo
            
            referencia = MedicamentoReferencia(
                nome_comercial='Cloridrato de Metadona 5mg',
                registro_ms='1.0244.0149.001',
                principio_ativo='Cloridrato de Metadona',
                tarja='Portaria 344',
                uso_continuo=False,
                tipo_receita="Receita 'A' (Amarela)",
                lista_portaria='A1',
            )
            db.session.add(referencia)
            db.session.commit()

            validade = date.today() + timedelta(days=180)
            status = calcular_status_semaforo(validade)
            medicamento = Medicamento(
                nome='Med Controlado',
                lote='TEST-005',
                data_validade=validade,
                quantidade=20,
                status_semaforo=status,
                tarja='Sem Tarja',
                principio_ativo='Cloridrato de Metadona',
                uso_continuo=False,
                referencia_id=referencia.id,
            )
            db.session.add(medicamento)
            with self.assertRaises(ValueError):
                db.session.commit()

    def test_medicamento_portaria_344_principio_ativo_requer_tarja(self):
        """Testa validação por princípio ativo sem referência."""
        with self.app.app_context():
            from app.utils.semaforo import calcular_status_semaforo
            
            referencia = MedicamentoReferencia(
                nome_comercial='Citrato de Fentanila 50mcg/mL',
                registro_ms='1.0244.0112.001',
                principio_ativo='Citrato de Fentanila',
                tarja='Portaria 344',
                uso_continuo=False,
                tipo_receita="Receita 'A' (Amarela)",
                lista_portaria='A1',
            )
            db.session.add(referencia)
            db.session.commit()

            validade = date.today() + timedelta(days=90)
            status = calcular_status_semaforo(validade)
            medicamento = Medicamento(
                nome='Fentanila 50mcg',
                lote='TEST-006',
                data_validade=validade,
                quantidade=5,
                status_semaforo=status,
                tarja='Sem Tarja',
                principio_ativo='Citrato de Fentanila',
                uso_continuo=False,
            )
            db.session.add(medicamento)
            with self.assertRaises(ValueError):
                db.session.commit()
    
    def test_paciente_creation(self):
        """Testa a criação de um paciente"""
        with self.app.app_context():
            paciente = Paciente(
                nome='João Silva',
                cpf='98765432100',
                data_nascimento=date(1990, 1, 1),
                endereco='Rua Teste, 123'
            )
            
            db.session.add(paciente)
            db.session.commit()
            
            # Verifica se foi salvo
            saved_paciente = Paciente.query.filter_by(cpf='98765432100').first()
            self.assertIsNotNone(saved_paciente)
            self.assertEqual(saved_paciente.nome, 'João Silva')
            self.assertEqual(saved_paciente.endereco, 'Rua Teste, 123')
    
    def test_medico_creation(self):
        """Testa a criação de um médico"""
        with self.app.app_context():
            medico = Medico(
                nome='Dr. Teste',
                crm='CRM-SP-123456',
                especialidade='Clínica Geral',
                contato='(15) 99999-9999'
            )
            
            db.session.add(medico)
            db.session.commit()
            
            # Verifica se foi salvo
            saved_medico = Medico.query.filter_by(crm='CRM-SP-123456').first()
            self.assertIsNotNone(saved_medico)
            self.assertEqual(saved_medico.nome, 'Dr. Teste')
            self.assertEqual(saved_medico.especialidade, 'Clínica Geral')
    
    def test_farmacia_creation(self):
        """Testa a criação de uma farmácia"""
        with self.app.app_context():
            farmacia = Farmacia(
                nome_fantasia='Farmácia Teste',
                razao_social='Farmácia Teste LTDA',
                cnpj='12.345.678/0001-90',
                endereco='Rua Farmácia, 456',
                responsavel='Responsável Teste'
            )
            
            db.session.add(farmacia)
            db.session.commit()
            
            # Verifica se foi salvo
            saved_farmacia = Farmacia.query.filter_by(cnpj='12.345.678/0001-90').first()
            self.assertIsNotNone(saved_farmacia)
            self.assertEqual(saved_farmacia.nome_fantasia, 'Farmácia Teste')
            self.assertEqual(saved_farmacia.responsavel, 'Responsável Teste')
    
    def test_doacao_creation(self):
        """Testa a criação de uma doação"""
        with self.app.app_context():
            from app.core.security import criptografar_senha
            from app.utils.semaforo import calcular_status_semaforo
            
            # Cria usuário e medicamento necessários
            usuario = Usuario(
                nome='Test User',
                cpf='12345678901',
                email='test@example.com',
                senha=criptografar_senha('password123'),
                cargo='Voluntário',
                ativo=True
            )
            
            validade = date.today() + timedelta(days=365)
            medicamento = Medicamento(
                nome='Test Medicamento',
                lote='TEST-002',
                data_validade=validade,
                quantidade=50,
                status_semaforo=calcular_status_semaforo(validade),
                tarja='Sem Tarja',
                principio_ativo='Test',
                uso_continuo=False
            )
            
            db.session.add(usuario)
            db.session.add(medicamento)
            db.session.commit()
            
            # Cria doação
            doacao = Doacao(
                usuario_id=usuario.id,
                medicamento_id=medicamento.id,
                quantidade=10,
                data_doacao=datetime.now()
            )
            
            db.session.add(doacao)
            db.session.commit()
            
            # Verifica se foi salva
            saved_doacao = Doacao.query.filter_by(usuario_id=usuario.id).first()
            self.assertIsNotNone(saved_doacao)
            self.assertEqual(saved_doacao.quantidade, 10)
            self.assertEqual(saved_doacao.medicamento_id, medicamento.id)
    
    def test_log_atividade_creation(self):
        """Testa a criação de um log de atividade"""
        with self.app.app_context():
            log = LogAtividade(
                usuario_id=None,
                acao='Test Action',
                detalhes='Test details',
                ip='127.0.0.1'
            )
            
            db.session.add(log)
            db.session.commit()
            
            # Verifica se foi salvo
            saved_log = LogAtividade.query.filter_by(acao='Test Action').first()
            self.assertIsNotNone(saved_log)
            self.assertEqual(saved_log.detalhes, 'Test details')
            self.assertEqual(saved_log.ip, '127.0.0.1')
    
    def test_usuario_relationships(self):
        """Testa relacionamentos do usuário"""
        with self.app.app_context():
            from app.core.security import criptografar_senha
            from app.utils.semaforo import calcular_status_semaforo
            
            usuario = Usuario(
                nome='Test User',
                cpf='12345678901',
                email='test@example.com',
                senha=criptografar_senha('password123'),
                cargo='Voluntário',
                ativo=True
            )
            
            validade = date.today() + timedelta(days=365)
            medicamento = Medicamento(
                nome='Test Medicamento',
                lote='TEST-003',
                data_validade=validade,
                quantidade=50,
                status_semaforo=calcular_status_semaforo(validade),
                tarja='Sem Tarja',
                principio_ativo='Test',
                uso_continuo=False
            )
            
            db.session.add(usuario)
            db.session.add(medicamento)
            db.session.commit()
            
            doacao = Doacao(
                usuario_id=usuario.id,
                medicamento_id=medicamento.id,
                quantidade=5,
                data_doacao=datetime.now()
            )
            
            db.session.add(doacao)
            db.session.commit()
            
            # Verifica relacionamento
            saved_usuario = Usuario.query.filter_by(cpf='12345678901').first()
            self.assertEqual(len(saved_usuario.doacoes), 1)
            self.assertEqual(saved_usuario.doacoes[0].quantidade, 5)


if __name__ == '__main__':
    unittest.main(verbosity=2)
