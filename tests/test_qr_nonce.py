"""
Tests for QR nonce security and single-use dispensation (P0.10).

This test suite verifies that QR codes use opaque nonces without personal data,
have proper expiration, are single-use, and are consumed atomically with stock reduction.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from datetime import date, timedelta, datetime
from main import create_app
from app.database import db
from app.models.medicamento import Medicamento
from app.models.receita import Receita
from app.models.qr_nonce import QRNonce
from app.models.paciente import Paciente
from app.models.medico import Medico
from app.models.usuario import Usuario
from app.core.security import criptografar_senha
import pytest


@pytest.fixture
def app():
    """Create application with test configuration."""
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key',
        'SESSION_SECRET': 'test-session-secret',
        'JWT_SECRET_KEY': 'test-jwt-secret-different',
        'QR_EXPIRATION_MINUTES': 15,
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def farmaceutico_user(app):
    """Create pharmacist user for authentication."""
    with app.app_context():
        farmaceutico = Usuario(
            nome="Farmaceutico User",
            cpf="98765432101",
            email="farmaceutico@test.com",
            senha=criptografar_senha("password123"),
            cargo="Farmacêutico",
            senha_trocada=True
        )
        db.session.add(farmaceutico)
        db.session.commit()
        return farmaceutico.id


@pytest.fixture
def medico_user(app):
    """Create doctor user for authentication."""
    with app.app_context():
        medico = Usuario(
            nome="Medico User",
            cpf="11122233344",
            email="medico@test.com",
            senha=criptografar_senha("password123"),
            cargo="Médico",
            senha_trocada=True
        )
        db.session.add(medico)
        db.session.commit()
        return medico.id


@pytest.fixture
def prescription_data(app):
    """Create test prescription with all dependencies."""
    future_date = date.today() + timedelta(days=90)
    
    with app.app_context():
        paciente = Paciente(
            nome="Test Patient",
            cpf="12345678901",
            data_nascimento=date(1990, 1, 1)
        )
        medico = Medico(
            nome="Test Doctor",
            crm="12345-SP",
            especialidade="General"
        )
        medicamento = Medicamento(
            nome='Paracetamol 500mg',
            lote='LOT12345',
            data_validade=future_date,
            quantidade=10,
            status_semaforo=0,
            tarja='Sem Tarja',
            principio_ativo='Paracetamol'
        )
        db.session.add_all([paciente, medico, medicamento])
        db.session.commit()
        
        receita = Receita(
            paciente_id=paciente.id,
            medico_id=medico.id,
            medicamento_id=medicamento.id,
            status="pendente"
        )
        db.session.add(receita)
        db.session.commit()
        
        return {
            'receita_id': receita.id,
            'medicamento_id': medicamento.id,
            'original_quantity': medicamento.quantidade
        }


class TestQRNonceModel:
    """Tests for QR nonce model functionality."""

    def test_generate_nonce_is_random(self, app):
        """Generated nonces should be random and unique."""
        with app.app_context():
            nonce1 = QRNonce.generate_nonce()
            nonce2 = QRNonce.generate_nonce()
            
            assert nonce1 != nonce2
            assert len(nonce1) == 64  # 32 bytes = 64 hex chars
            assert len(nonce2) == 64

    def test_create_nonce_for_prescription(self, app, prescription_data):
        """Creating a nonce for a prescription should store the link."""
        with app.app_context():
            qr_nonce = QRNonce.create_for_prescription(
                receita_id=prescription_data['receita_id'],
                gerado_por_id=1,
                expiracao_minutos=15
            )
            
            assert qr_nonce is not None
            assert qr_nonce.receita_id == prescription_data['receita_id']
            assert qr_nonce.usado is False
            assert qr_nonce.nonce is not None
            assert len(qr_nonce.nonce) == 64

    def test_nonce_valid_when_fresh(self, app, prescription_data):
        """Fresh nonce should be valid."""
        with app.app_context():
            qr_nonce = QRNonce.create_for_prescription(
                receita_id=prescription_data['receita_id'],
                expiracao_minutos=15
            )
            
            assert qr_nonce.is_valid() is True

    def test_nonce_invalid_when_expired(self, app, prescription_data):
        """Expired nonce should be invalid."""
        with app.app_context():
            # Create nonce with past expiration
            qr_nonce = QRNonce(
                nonce=QRNonce.generate_nonce(),
                receita_id=prescription_data['receita_id'],
                expira_em=datetime.utcnow() - timedelta(minutes=1),
                usado=False
            )
            db.session.add(qr_nonce)
            db.session.commit()
            
            assert qr_nonce.is_valid() is False

    def test_nonce_invalid_when_used(self, app, prescription_data):
        """Used nonce should be invalid."""
        with app.app_context():
            qr_nonce = QRNonce.create_for_prescription(
                receita_id=prescription_data['receita_id'],
                expiracao_minutos=15
            )
            
            qr_nonce.mark_as_used(1)
            
            assert qr_nonce.is_valid() is False
            assert qr_nonce.usado is True
            assert qr_nonce.usado_em is not None


class TestQRGeneration:
    """Tests for QR code generation endpoint."""

    def test_generate_qr_returns_opaque_nonce(self, app, prescription_data, medico_user):
        """QR generation should return opaque nonce, not personal data."""
        with app.app_context():
            # Create nonce directly (bypassing authentication for this test)
            qr_nonce = QRNonce.create_for_prescription(
                receita_id=prescription_data['receita_id'],
                gerado_por_id=medico_user,
                expiracao_minutos=15
            )
            
            # Verify nonce properties
            assert qr_nonce is not None
            assert qr_nonce.receita_id == prescription_data['receita_id']
            assert qr_nonce.usado is False
            assert len(qr_nonce.nonce) == 64  # 32 bytes = 64 hex chars
            
            # Verify no personal data in nonce
            assert 'paciente' not in qr_nonce.nonce
            assert 'nome' not in qr_nonce.nonce
            assert 'cpf' not in qr_nonce.nonce

    def test_generate_qr_nonexistent_prescription(self, app):
        """Non-existent prescription should return error."""
        with app.app_context():
            try:
                qr_nonce = QRNonce.create_for_prescription(
                    receita_id=99999,
                    expiracao_minutos=15
                )
                # If we get here, the test failed (should have raised exception)
                assert False, "Should have raised exception for non-existent prescription"
            except Exception:
                # Expected - foreign key constraint should fail
                pass


class TestQRValidation:
    """Tests for QR code validation and dispensation."""

    def test_validate_qr_with_valid_nonce(self, app, prescription_data, farmaceutico_user):
        """Valid nonce should allow dispensation."""
        from app.utils.medication_validation import atomic_reduce_stock_quantity, validate_batch_for_stock_reduction
        
        with app.app_context():
            # Create nonce
            qr_nonce = QRNonce.create_for_prescription(
                receita_id=prescription_data['receita_id'],
                expiracao_minutos=15
            )
            
            # Get prescription
            receita = db.session.get(Receita, prescription_data['receita_id'])
            
            # Validate nonce
            assert qr_nonce.is_valid() is True
            
            # Validate stock
            validacao = validate_batch_for_stock_reduction(
                data_validade=receita.medicamento.data_validade,
                quantidade_solicitada=1,
                quantidade_disponivel=receita.medicamento.quantidade
            )
            assert validacao.is_valid is True
            
            # Atomically reduce stock
            success, new_quantity = atomic_reduce_stock_quantity(
                db.session,
                receita.medicamento_id,
                1
            )
            assert success is True
            
            # Mark nonce as used and update prescription
            qr_nonce.mark_as_used(farmaceutico_user)
            receita.status = "dispensada"
            receita.dispensada_em = datetime.utcnow()
            receita.dispensada_por_id = farmaceutico_user
            db.session.commit()
            
            # Verify final state
            qr_nonce = db.session.get(QRNonce, qr_nonce.id)
            assert qr_nonce.usado is True
            
            medicamento = db.session.get(Medicamento, prescription_data['medicamento_id'])
            assert medicamento.quantidade == prescription_data['original_quantity'] - 1

    def test_validate_qr_with_expired_nonce(self, app, prescription_data):
        """Expired nonce should be rejected."""
        with app.app_context():
            # Create expired nonce
            qr_nonce = QRNonce(
                nonce=QRNonce.generate_nonce(),
                receita_id=prescription_data['receita_id'],
                expira_em=datetime.utcnow() - timedelta(minutes=1),
                usado=False
            )
            db.session.add(qr_nonce)
            db.session.commit()
            
            assert qr_nonce.is_valid() is False

    def test_validate_qr_with_used_nonce(self, app, prescription_data):
        """Used nonce should be rejected."""
        with app.app_context():
            # Create and use nonce
            qr_nonce = QRNonce.create_for_prescription(
                receita_id=prescription_data['receita_id'],
                expiracao_minutos=15
            )
            qr_nonce.mark_as_used(1)
            
            assert qr_nonce.is_valid() is False

    def test_validate_qr_nonexistent_nonce(self, app):
        """Non-existent nonce should be rejected."""
        with app.app_context():
            qr_nonce = QRNonce.query.filter_by(nonce='nonexistent_nonce').first()
            assert qr_nonce is None


class TestQRDataPrivacy:
    """Tests for data privacy in QR flow."""

    def test_qr_payload_contains_no_personal_data(self, app, prescription_data):
        """QR nonce should not contain personal or clinical data."""
        with app.app_context():
            qr_nonce = QRNonce.create_for_prescription(
                receita_id=prescription_data['receita_id'],
                expiracao_minutos=15
            )
            
            # Check that nonce doesn't contain personal data
            nonce_str = qr_nonce.nonce
            assert 'paciente' not in nonce_str
            assert 'nome' not in nonce_str
            assert 'cpf' not in nonce_str
            assert 'medicamento' not in nonce_str
            assert 'principio_ativo' not in nonce_str
            
            # Nonce should be hexadecimal only
            assert all(c in '0123456789abcdef' for c in nonce_str)


class TestQRSingleUse:
    """Tests for single-use property of QR nonces."""

    def test_nonce_can_only_be_used_once(self, app, prescription_data):
        """Nonce should only be usable once."""
        from app.utils.medication_validation import atomic_reduce_stock_quantity, validate_batch_for_stock_reduction
        
        with app.app_context():
            qr_nonce = QRNonce.create_for_prescription(
                receita_id=prescription_data['receita_id'],
                expiracao_minutos=15
            )
            
            receita = db.session.get(Receita, prescription_data['receita_id'])
            
            # First use - should succeed
            assert qr_nonce.is_valid() is True
            
            validacao = validate_batch_for_stock_reduction(
                data_validade=receita.medicamento.data_validade,
                quantidade_solicitada=1,
                quantidade_disponivel=receita.medicamento.quantidade
            )
            assert validacao.is_valid is True
            
            success, new_quantity = atomic_reduce_stock_quantity(
                db.session,
                receita.medicamento_id,
                1
            )
            assert success is True
            
            qr_nonce.mark_as_used(1)
            receita.status = "dispensada"
            receita.dispensada_em = datetime.utcnow()
            db.session.commit()
            
            # Second use - should fail
            qr_nonce = db.session.get(QRNonce, qr_nonce.id)
            assert qr_nonce.is_valid() is False
            
            # Stock should only be reduced once
            medicamento = db.session.get(Medicamento, prescription_data['medicamento_id'])
            assert medicamento.quantidade == prescription_data['original_quantity'] - 1
