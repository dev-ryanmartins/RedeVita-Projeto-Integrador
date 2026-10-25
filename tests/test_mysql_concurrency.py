"""
Tests for P0.9 concurrency validation on MySQL 8.0.

This test suite verifies that stock reduction operations are atomic
under real concurrent access using MySQL 8.0 with InnoDB engine.
These tests are designed to run in CI with a disposable MySQL instance.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from datetime import date, timedelta
from main import create_app
from app.database import db
from app.models.medicamento import Medicamento
from app.models.usuario import Usuario
from app.models.receita import Receita
from app.models.paciente import Paciente
from app.models.medico import Medico
from app.models.qr_nonce import QRNonce
from app.core.security import criptografar_senha
from app.utils.medication_validation import atomic_reduce_stock_quantity
import pytest
import threading
import time
import pymysql
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy import event

# MySQL test configuration - synthetic credentials only
MYSQL_HOST = os.environ.get('MYSQL_HOST', '127.0.0.1')
MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))
MYSQL_USER = os.environ.get('MYSQL_USER', 'test_user')
MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'test_password_123')
MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE', 'test_redevita')

MYSQL_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"


@pytest.fixture(scope="module")
def mysql_engine():
    """Create MySQL engine for concurrent testing."""
    if not MYSQL_DATABASE.startswith('test_'):
        pytest.skip("MySQL tests require test database name starting with 'test_'")
    
    engine = create_engine(
        MYSQL_URL,
        pool_pre_ping=True,
        pool_recycle=280,
        isolation_level="READ COMMITTED"
    )
    return engine


@pytest.fixture(scope="module")
def mysql_session_factory(mysql_engine):
    """Create session factory for MySQL."""
    return sessionmaker(bind=mysql_engine)


@pytest.fixture(scope="module", autouse=True)
def disable_portaria_validation():
    """
    Disable Portaria 344 validation for MySQL concurrency tests.

    The validation uses Flask-SQLAlchemy which requires application context,
    but these tests use independent SQLAlchemy sessions.
    """
    from app.models.medicamento import _validar_portaria_344_medicamento
    event.remove(Medicamento, 'before_insert', _validar_portaria_344_medicamento)
    event.remove(Medicamento, 'before_update', _validar_portaria_344_medicamento)
    yield
    # Event listeners are not restored since this is module-scoped and tests run in isolation


class TestMySQLConcurrency:
    """Tests for real concurrent stock reduction on MySQL 8.0."""

    def test_concurrent_last_unit_mysql(self, mysql_session_factory):
        """
        Two independent MySQL connections competing for the last unit.
        
        This test uses real concurrent transactions on MySQL 8.0 with InnoDB
        to verify that exactly one operation succeeds when two threads
        attempt to reduce stock when only 1 unit is available.
        """
        Session = mysql_session_factory
        
        # Setup: Create medication with 1 unit
        session1 = Session()
        try:
            future_date = date.today() + timedelta(days=90)
            medicamento = Medicamento(
                nome='Paracetamol 500mg',
                lote='LOT12345',
                data_validade=future_date,
                quantidade=1,  # Only 1 unit available
                status_semaforo=0,
                tarja='Sem Tarja',
                principio_ativo='Paracetamol',
                ativo=True
            )
            session1.add(medicamento)
            session1.commit()
            med_id = medicamento.id
        finally:
            session1.close()
        
        results = []
        errors = []
        barrier = threading.Barrier(2)  # Synchronize threads to start simultaneously
        
        def reduce_stock_thread(thread_id):
            """Thread function using independent MySQL connection."""
            session = Session()
            try:
                # Wait for both threads to be ready
                barrier.wait(timeout=5)
                
                # Attempt atomic reduction
                success, new_quantity = atomic_reduce_stock_quantity(
                    session,
                    med_id,
                    1
                )
                
                if success:
                    session.commit()
                else:
                    session.rollback()
                
                results.append((thread_id, success, new_quantity))
            except Exception as e:
                errors.append((thread_id, str(e)))
                session.rollback()
            finally:
                session.close()
        
        # Create two threads with independent connections
        thread1 = threading.Thread(target=reduce_stock_thread, args=(1,))
        thread2 = threading.Thread(target=reduce_stock_thread, args=(2,))
        
        # Start both threads
        thread1.start()
        thread2.start()
        
        # Wait for both to complete
        thread1.join(timeout=10)
        thread2.join(timeout=10)
        
        # Verify no errors
        assert len(errors) == 0, f"Errors occurred: {errors}"
        
        # Verify both threads attempted
        assert len(results) == 2, f"Expected 2 results, got {len(results)}"
        
        # Count successes
        success_count = sum(1 for _, success, _ in results if success)
        
        # EXACTLY one should succeed (atomic condition prevents overdraw)
        assert success_count == 1, f"Expected exactly 1 success, got {success_count}. Results: {results}"
        
        # Verify final quantity is non-negative
        session_check = Session()
        try:
            medicamento = session_check.query(Medicamento).get(med_id)
            assert medicamento is not None, "Medicamento should still exist"
            assert medicamento.quantidade >= 0, f"Final quantity should be non-negative, got {medicamento.quantidade}"
            assert medicamento.quantidade == 0, f"Final quantity should be 0, got {medicamento.quantidade}"
        finally:
            session_check.close()
    
    def test_concurrent_idempotent_qr_dispensation_mysql(self, mysql_session_factory):
        """
        Concurrent repeated QR dispensation should not duplicate stock reduction.
        
        This test verifies that if the same prescription is dispensed
        concurrently by two threads (e.g., due to network retry), the stock
        is only reduced once.
        """
        Session = mysql_session_factory
        
        # Setup: Create entities
        session1 = Session()
        try:
            future_date = date.today() + timedelta(days=90)
            
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
                principio_ativo='Paracetamol',
                ativo=True
            )
            session1.add_all([paciente, medico, medicamento])
            session1.commit()
            
            receita = Receita(
                paciente_id=paciente.id,
                medico_id=medico.id,
                medicamento_id=medicamento.id,
                status="pendente"
            )
            session1.add(receita)
            session1.commit()
            
            receita_id = receita.id
            med_id = medicamento.id
            original_quantity = medicamento.quantidade
        finally:
            session1.close()
        
        barrier = threading.Barrier(2)
        results = []
        
        def dispense_thread(thread_id):
            """Thread function for concurrent dispensation."""
            session = Session()
            try:
                barrier.wait(timeout=5)
                
                # Check idempotency and attempt dispensation
                receita = session.query(Receita).get(receita_id)
                
                if receita.status == "dispensada":
                    # Already dispensed - should not reduce stock
                    results.append((thread_id, "already_dispensed"))
                    session.rollback()
                else:
                    success, new_quantity = atomic_reduce_stock_quantity(
                        session,
                        med_id,
                        1
                    )
                    if success:
                        receita.status = "dispensada"
                        receita.dispensada_em = date.today()
                        session.commit()
                        results.append((thread_id, "success"))
                    else:
                        session.rollback()
                        results.append((thread_id, "insufficient_stock"))
            except Exception as e:
                results.append((thread_id, f"error: {str(e)}"))
                session.rollback()
            finally:
                session.close()
        
        # Two threads attempt concurrent dispensation
        thread1 = threading.Thread(target=dispense_thread, args=(1,))
        thread2 = threading.Thread(target=dispense_thread, args=(2,))
        
        thread1.start()
        thread2.start()
        thread1.join(timeout=10)
        thread2.join(timeout=10)
        
        # Verify exactly one succeeded
        success_count = sum(1 for _, result in results if result == "success")
        assert success_count == 1, f"Expected exactly 1 success, got {success_count}. Results: {results}"
        
        # Verify stock was only reduced once
        session_check = Session()
        try:
            medicamento = session_check.query(Medicamento).get(med_id)
            assert medicamento.quantidade == original_quantity - 1, \
                f"Stock should be reduced by 1, got {medicamento.quantidade} from {original_quantity}"
        finally:
            session_check.close()
    
    def test_mysql_engine_isolation_level(self, mysql_engine):
        """
        Verify MySQL uses InnoDB engine and appropriate isolation level.
        """
        # Check engine type
        with mysql_engine.connect() as conn:
            result = conn.execute(
                text("SELECT ENGINE FROM information_schema.TABLES "
                     "WHERE TABLE_SCHEMA = :db_name AND TABLE_NAME = 'medicamentos'"),
                {"db_name": MYSQL_DATABASE}
            )
            engine_info = result.fetchone()
            assert engine_info is not None, "medicamentos table should exist"
            assert engine_info[0] == 'InnoDB', f"Expected InnoDB engine, got {engine_info[0]}"

        # Verify isolation level
        with mysql_engine.connect() as conn:
            result = conn.execute(text("SELECT @@transaction_isolation"))
            isolation = result.fetchone()
            assert isolation is not None, "Should be able to query isolation level"
            assert 'READ COMMITTED' in str(isolation[0]) or 'REPEATABLE READ' in str(isolation[0]), \
                f"Expected READ COMMITTED or REPEATABLE READ, got {isolation[0]}"
    
    def test_concurrent_qr_consumption_mysql(self, mysql_session_factory):
        """
        Two independent MySQL connections competing to consume the same QR nonce.
        
        This test uses real concurrent transactions on MySQL 8.0 with InnoDB
        to verify that exactly one dispensation succeeds when two threads
        attempt to consume the same QR nonce for the last unit of stock.
        """
        Session = mysql_session_factory
        
        # Setup: Create medication with 1 unit and prescription
        session1 = Session()
        try:
            future_date = date.today() + timedelta(days=90)
            medicamento = Medicamento(
                nome='Paracetamol 500mg',
                lote='LOT12345',
                data_validade=future_date,
                quantidade=1,  # Only 1 unit available
                status_semaforo=0,
                tarja='Sem Tarja',
                principio_ativo='Paracetamol',
                ativo=True
            )
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
            session1.add_all([medicamento, paciente, medico])
            session1.commit()
            
            receita = Receita(
                paciente_id=paciente.id,
                medico_id=medico.id,
                medicamento_id=medicamento.id,
                status="pendente"
            )
            session1.add(receita)
            session1.commit()
            
            # Create QR nonce
            qr_nonce = QRNonce(
                nonce=QRNonce.generate_nonce(),
                receita_id=receita.id,
                expira_em=date.today() + timedelta(days=1),
                usado=False
            )
            session1.add(qr_nonce)
            session1.commit()
            
            nonce_str = qr_nonce.nonce
            receita_id = receita.id
            med_id = medicamento.id
            original_quantity = medicamento.quantidade
        finally:
            session1.close()
        
        barrier = threading.Barrier(2)
        results = []
        
        def consume_qr_thread(thread_id):
            """Thread function for concurrent QR consumption."""
            session = Session()
            try:
                barrier.wait(timeout=5)
                
                # Try to consume the QR nonce
                qr_nonce = session.query(QRNonce).filter_by(nonce=nonce_str).first()
                
                if not qr_nonce:
                    results.append((thread_id, "nonce_not_found"))
                    session.rollback()
                    return
                
                if not qr_nonce.is_valid():
                    results.append((thread_id, "nonce_invalid"))
                    session.rollback()
                    return
                
                receita = session.query(Receita).get(receita_id)
                
                if receita.status == "dispensada":
                    results.append((thread_id, "already_dispensed"))
                    session.rollback()
                    return
                
                # Attempt atomic stock reduction
                success, new_quantity = atomic_reduce_stock_quantity(
                    session,
                    med_id,
                    1
                )
                
                if success:
                    # Mark nonce as used and update prescription
                    qr_nonce.usado = True
                    qr_nonce.usado_em = date.today()
                    qr_nonce.usado_por_id = 1
                    receita.status = "dispensada"
                    receita.dispensada_em = date.today()
                    session.commit()
                    results.append((thread_id, "success"))
                else:
                    session.rollback()
                    results.append((thread_id, "insufficient_stock"))
            except Exception as e:
                results.append((thread_id, f"error: {str(e)}"))
                session.rollback()
            finally:
                session.close()
        
        # Two threads attempt concurrent QR consumption
        thread1 = threading.Thread(target=consume_qr_thread, args=(1,))
        thread2 = threading.Thread(target=consume_qr_thread, args=(2,))
        
        thread1.start()
        thread2.start()
        thread1.join(timeout=10)
        thread2.join(timeout=10)
        
        # Verify exactly one succeeded
        success_count = sum(1 for _, result in results if result == "success")
        assert success_count == 1, f"Expected exactly 1 success, got {success_count}. Results: {results}"
        
        # Verify stock was only reduced once
        session_check = Session()
        try:
            medicamento = session_check.query(Medicamento).get(med_id)
            assert medicamento.quantidade == original_quantity - 1, \
                f"Stock should be reduced by 1, got {medicamento.quantidade} from {original_quantity}"
            
            # Verify prescription was marked as dispensed
            receita = session_check.query(Receita).get(receita_id)
            assert receita.status == "dispensada", "Prescription should be marked as dispensed"
            
            # Verify nonce was marked as used
            qr_nonce = session_check.query(QRNonce).filter_by(nonce=nonce_str).first()
            assert qr_nonce.usado is True, "Nonce should be marked as used"
        finally:
            session_check.close()
    
    def test_concurrent_cancellation_not_implemented(self, mysql_session_factory):
        """
        BLOCKER: Cancellation flow is not implemented in routes.

        The models Doacao and SolicitacaoEstoque have cancellation fields,
        but there are no routes implementing cancellation logic.
        Therefore, concurrent cancellation cannot be tested.
        """
        pytest.skip("Cancellation flow not implemented in routes - BLOCKER for P0.9")
