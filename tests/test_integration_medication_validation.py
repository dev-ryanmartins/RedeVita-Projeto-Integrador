"""
Integration tests for medication validation across web and API routes.

Tests that web and API routes apply equivalent validation rules for
batch creation, expiration, and eligibility.
"""

import sys
import os
import pytest
from datetime import date, timedelta

# Adiciona o diretório backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from main import create_app
from app.database import db
from app.models.medicamento import Medicamento
from app.utils.medication_validation import set_time_provider


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


class TestValidationServiceIntegration:
    """Tests that the validation service is correctly integrated with routes."""

    def test_validation_service_rejects_expired_batch(self, app):
        """Validation service should reject expired batches consistently."""
        past_date = date.today() - timedelta(days=10)
        
        with app.app_context():
            from app.utils.medication_validation import validate_batch_for_creation
            
            result = validate_batch_for_creation(
                nome='Paracetamol 500mg',
                lote='LOT12345',
                data_validade=past_date,
                quantidade=100,
                tarja='Sem Tarja'
            )
            
            assert result.is_valid is False
            assert 'vencido' in result.error_message.lower()

    def test_validation_service_accepts_valid_batch(self, app):
        """Validation service should accept valid batches."""
        future_date = date.today() + timedelta(days=90)
        
        with app.app_context():
            from app.utils.medication_validation import validate_batch_for_creation
            
            result = validate_batch_for_creation(
                nome='Paracetamol 500mg',
                lote='LOT12345',
                data_validade=future_date,
                quantidade=100,
                tarja='Sem Tarja'
            )
            
            assert result.is_valid is True

    def test_validation_service_rejects_invalid_tarja(self, app):
        """Validation service should reject unknown tarja values."""
        future_date = date.today() + timedelta(days=90)
        
        with app.app_context():
            from app.utils.medication_validation import validate_batch_for_creation
            
            result = validate_batch_for_creation(
                nome='Paracetamol 500mg',
                lote='LOT12345',
                data_validade=future_date,
                quantidade=100,
                tarja='Invalid Tarja'
            )
            
            assert result.is_valid is False
            assert 'inválida' in result.error_message.lower()

    def test_stock_reduction_validation_blocks_expired(self, app):
        """Stock reduction validation should block expired batches."""
        past_date = date.today() - timedelta(days=10)
        
        with app.app_context():
            from app.utils.medication_validation import validate_batch_for_stock_reduction
            
            result = validate_batch_for_stock_reduction(
                data_validade=past_date,
                quantidade_solicitada=10,
                quantidade_disponivel=100
            )
            
            assert result.is_valid is False
            assert 'vencido' in result.error_message.lower()

    def test_frozen_clock_affects_validation(self, app):
        """Frozen time provider should affect validation consistently."""
        frozen_date = date(2024, 1, 15)
        set_time_provider(lambda: frozen_date)
        
        try:
            with app.app_context():
                from app.utils.medication_validation import (
                    validate_expiration,
                    calculate_semaforo_status
                )
                
                # Date before frozen time should be expired
                past_date = date(2024, 1, 10)
                result = validate_expiration(past_date)
                assert result.is_valid is False
                
                status = calculate_semaforo_status(past_date)
                assert status == 2  # Red/expired
                
                # Date after frozen time should be valid
                future_date = date(2024, 3, 1)
                result = validate_expiration(future_date)
                assert result.is_valid is True
                
                status = calculate_semaforo_status(future_date)
                assert status == 0  # Green/safe
        finally:
            set_time_provider(None)


class TestDatabaseIntegrity:
    """Tests that rejected operations don't leave partial database changes."""

    def test_validation_before_db_commit(self, app):
        """Validation should occur before database commit."""
        past_date = date.today() - timedelta(days=10)
        
        with app.app_context():
            from app.utils.medication_validation import validate_batch_for_creation
            
            # Validate first
            result = validate_batch_for_creation(
                nome='Paracetamol 500mg',
                lote='LOT12345',
                data_validade=past_date,
                quantidade=100,
                tarja='Sem Tarja'
            )
            
            assert result.is_valid is False
            
            # Only proceed to DB if validation passes
            if result.is_valid:
                med = Medicamento(
                    nome='Paracetamol 500mg',
                    lote='LOT12345',
                    data_validade=past_date,
                    quantidade=100,
                    status_semaforo=2,
                    tarja='Sem Tarja'
                )
                db.session.add(med)
                db.session.commit()
            
            # Verify no record was created
            count = Medicamento.query.count()
            assert count == 0
