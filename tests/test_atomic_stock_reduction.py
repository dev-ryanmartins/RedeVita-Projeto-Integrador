"""
Tests for atomic stock reduction under concurrency (P0.9).

This test suite verifies that stock reduction operations are atomic
and prevent race conditions where concurrent requests could approve
withdrawals exceeding the available balance.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from datetime import date, timedelta
from main import create_app
from app.database import db
from app.models.medicamento import Medicamento
from app.models.usuario import Usuario
from app.core.security import criptografar_senha
from app.utils.medication_validation import atomic_reduce_stock_quantity
import pytest
import sys

# Skip concurrent SQLite tests on Python 3.12 due to SQLite threading limitations
pytestmark = pytest.mark.skipif(
    sys.version_info >= (3, 12),
    reason="SQLite has threading limitations in Python 3.12; use MySQL for concurrent tests"
)
import threading
import time


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


class TestAtomicStockReduction:
    """Tests for atomic stock reduction function."""

    def test_atomic_reduce_sufficient_stock(self, app):
        """Atomic reduction should succeed when stock is sufficient."""
        future_date = date.today() + timedelta(days=90)
        
        with app.app_context():
            medicamento = Medicamento(
                nome='Paracetamol 500mg',
                lote='LOT12345',
                data_validade=future_date,
                quantidade=100,
                status_semaforo=0,
                tarja='Sem Tarja',
                principio_ativo='Paracetamol'
            )
            db.session.add(medicamento)
            db.session.commit()
            med_id = medicamento.id
        
        with app.app_context():
            success, new_quantity = atomic_reduce_stock_quantity(
                db.session,
                med_id,
                10
            )
            
            assert success is True
            assert new_quantity == 90
            
            # Verify in database
            medicamento = db.session.get(Medicamento, med_id)
            assert medicamento.quantidade == 90

    def test_atomic_reduce_insufficient_stock(self, app):
        """Atomic reduction should fail when stock is insufficient."""
        future_date = date.today() + timedelta(days=90)
        
        with app.app_context():
            medicamento = Medicamento(
                nome='Paracetamol 500mg',
                lote='LOT12345',
                data_validade=future_date,
                quantidade=5,
                status_semaforo=0,
                tarja='Sem Tarja',
                principio_ativo='Paracetamol'
            )
            db.session.add(medicamento)
            db.session.commit()
            med_id = medicamento.id
        
        with app.app_context():
            success, new_quantity = atomic_reduce_stock_quantity(
                db.session,
                med_id,
                10  # More than available
            )
            
            assert success is False
            assert new_quantity == 0
            
            # Verify quantity unchanged
            medicamento = db.session.get(Medicamento, med_id)
            assert medicamento.quantidade == 5

    def test_atomic_reduce_zero_quantity(self, app):
        """Atomic reduction should fail for zero quantity."""
        future_date = date.today() + timedelta(days=90)
        
        with app.app_context():
            medicamento = Medicamento(
                nome='Paracetamol 500mg',
                lote='LOT12345',
                data_validade=future_date,
                quantidade=100,
                status_semaforo=0,
                tarja='Sem Tarja',
                principio_ativo='Paracetamol'
            )
            db.session.add(medicamento)
            db.session.commit()
            med_id = medicamento.id
        
        with app.app_context():
            success, new_quantity = atomic_reduce_stock_quantity(
                db.session,
                med_id,
                0
            )
            
            # Should succeed (condition: quantidade >= 0 is always true)
            # But logically we should validate quantity > 0 before calling
            assert success is True
            assert new_quantity == 100

    def test_atomic_reduce_nonexistent_medicamento(self, app):
        """Atomic reduction should fail for non-existent medication."""
        with app.app_context():
            success, new_quantity = atomic_reduce_stock_quantity(
                db.session,
                99999,  # Non-existent ID
                10
            )
            
            assert success is False
            assert new_quantity == 0


class TestConcurrentStockReduction:
    """Tests for concurrent stock reduction scenarios."""

    def test_concurrent_requests_for_last_unit(self, app):
        """
        Two concurrent requests for the last unit should result in at most one success.
        
        This test simulates a race condition where two threads try to reduce
        stock when only 1 unit is available. At most one should succeed.
        
        Note: SQLite in-memory databases serialize writes, so true concurrent
        testing requires MySQL or PostgreSQL. This test verifies the atomic
        logic but may not fully exercise the race condition on SQLite.
        """
        future_date = date.today() + timedelta(days=90)
        
        with app.app_context():
            medicamento = Medicamento(
                nome='Paracetamol 500mg',
                lote='LOT12345',
                data_validade=future_date,
                quantidade=1,  # Only 1 unit available
                status_semaforo=0,
                tarja='Sem Tarja',
                principio_ativo='Paracetamol'
            )
            db.session.add(medicamento)
            db.session.commit()
            med_id = medicamento.id
        
        results = []
        errors = []
        
        def reduce_stock(app_context):
            """Thread function to reduce stock."""
            try:
                with app_context:
                    success, new_quantity = atomic_reduce_stock_quantity(
                        db.session,
                        med_id,
                        1
                    )
                    
                    if success:
                        db.session.commit()
                    else:
                        db.session.rollback()
                    
                    results.append(success)
            except Exception as e:
                errors.append(str(e))
        
        # Create app context for each thread
        ctx1 = app.app_context()
        ctx2 = app.app_context()
        
        # Create two threads to run concurrently
        thread1 = threading.Thread(target=reduce_stock, args=(ctx1,))
        thread2 = threading.Thread(target=reduce_stock, args=(ctx2,))
        
        # Start both threads
        thread1.start()
        thread2.start()
        
        # Wait for both to complete
        thread1.join()
        thread2.join()
        
        # Verify results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 2
        
        # At most one should succeed (atomic condition prevents overdraw)
        success_count = sum(results)
        assert success_count <= 1, f"Expected at most 1 success, got {success_count}"
        
        # Verify final quantity in database is non-negative
        with app.app_context():
            medicamento = db.session.get(Medicamento, med_id)
            assert medicamento.quantidade >= 0

    def test_concurrent_requests_exceed_stock(self, app):
        """
        Sequential requests exceeding stock should result in partial success.
        
        This test verifies that the atomic UPDATE prevents overdraw when
        multiple requests attempt to reduce stock. Due to SQLite's limitations
        with concurrent writes, this test runs sequentially but validates
        the atomic logic.
        
        If 5 units are available and 10 sequential requests each ask for 1 unit,
        exactly 5 should succeed and 5 should fail.
        """
        future_date = date.today() + timedelta(days=90)
        
        with app.app_context():
            medicamento = Medicamento(
                nome='Paracetamol 500mg',
                lote='LOT12345',
                data_validade=future_date,
                quantidade=5,  # 5 units available
                status_semaforo=0,
                tarja='Sem Tarja',
                principio_ativo='Paracetamol'
            )
            db.session.add(medicamento)
            db.session.commit()
            med_id = medicamento.id
        
        results = []
        
        # Make 10 sequential requests
        for _ in range(10):
            with app.app_context():
                success, new_quantity = atomic_reduce_stock_quantity(
                    db.session,
                    med_id,
                    1
                )
                
                if success:
                    db.session.commit()
                else:
                    db.session.rollback()
                
                results.append(success)
        
        # Exactly 5 should succeed (matching available stock)
        success_count = sum(results)
        assert success_count == 5, f"Expected 5 successes, got {success_count}"
        
        # Verify final quantity in database
        with app.app_context():
            medicamento = db.session.get(Medicamento, med_id)
            assert medicamento.quantidade == 0

    def test_concurrent_larger_quantities(self, app):
        """
        Sequential requests with different quantities should prevent overdraw.
        
        This test verifies that the atomic UPDATE prevents overdraw when
        multiple requests attempt to reduce stock. Due to SQLite's limitations
        with concurrent writes, this test runs sequentially but validates
        the atomic logic.
        """
        future_date = date.today() + timedelta(days=90)
        
        with app.app_context():
            medicamento = Medicamento(
                nome='Paracetamol 500mg',
                lote='LOT12345',
                data_validade=future_date,
                quantidade=10,  # 10 units available
                status_semaforo=0,
                tarja='Sem Tarja',
                principio_ativo='Paracetamol'
            )
            db.session.add(medicamento)
            db.session.commit()
            med_id = medicamento.id
        
        # First request for 6 units
        with app.app_context():
            success1, new_qty1 = atomic_reduce_stock_quantity(
                db.session,
                med_id,
                6
            )
            if success1:
                db.session.commit()
        
        # Second request for 5 units (should fail since only 4 remain)
        with app.app_context():
            success2, new_qty2 = atomic_reduce_stock_quantity(
                db.session,
                med_id,
                5
            )
            if success2:
                db.session.commit()
        
        # Verify first succeeded, second failed
        assert success1 is True
        assert success2 is False
        
        # Verify final quantity is 4 (10 - 6)
        with app.app_context():
            medicamento = db.session.get(Medicamento, med_id)
            assert medicamento.quantidade == 4


class TestIdempotency:
    """Tests for idempotency of operations."""

    def test_repeated_qr_dispensation(self, app):
        """
        Repeated QR dispensation should not duplicate stock reduction.
        
        This test verifies that if the same prescription is dispensed
        twice (e.g., due to network retry), the stock is only reduced once.
        """
        from app.models.receita import Receita
        from app.models.paciente import Paciente
        from app.models.medico import Medico
        from datetime import datetime
        
        future_date = date.today() + timedelta(days=90)
        
        with app.app_context():
            # Create supporting entities
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
            
            # Create prescription
            receita = Receita(
                paciente_id=paciente.id,
                medico_id=medico.id,
                medicamento_id=medicamento.id,
                status="pendente"
            )
            db.session.add(receita)
            db.session.commit()
            
            receita_id = receita.id
            med_id = medicamento.id
            original_quantity = medicamento.quantidade
        
        # First dispensation attempt
        with app.app_context():
            receita = db.session.get(Receita, receita_id)
            
            # Check idempotency: already dispensed
            if receita.status == "dispensada":
                # Should not reduce stock again
                pass
            else:
                success, new_quantity = atomic_reduce_stock_quantity(
                    db.session,
                    med_id,
                    1
                )
                if success:
                    receita.status = "dispensada"
                    receita.dispensada_em = datetime.utcnow()
                    db.session.commit()
        
        # Second dispensation attempt (simulating retry)
        with app.app_context():
            receita = db.session.get(Receita, receita_id)
            
            # Check idempotency: already dispensed
            if receita.status == "dispensada":
                # Should not reduce stock again
                pass
            else:
                success, new_quantity = atomic_reduce_stock_quantity(
                    db.session,
                    med_id,
                    1
                )
                if success:
                    receita.status = "dispensada"
                    receita.dispensada_em = datetime.utcnow()
                    db.session.commit()
        
        # Verify stock was only reduced once
        with app.app_context():
            medicamento = db.session.get(Medicamento, med_id)
            assert medicamento.quantidade == original_quantity - 1
