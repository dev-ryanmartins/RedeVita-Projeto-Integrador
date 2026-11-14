"""
Unit tests for medication validation domain service.

Tests centralized validation rules for batch expiration, classification,
quantity, and eligibility across web and API routes.
"""

import pytest
from datetime import date, datetime, timedelta
from app.utils.medication_validation import (
    validate_expiration,
    validate_tarja,
    validate_quantity,
    validate_batch_for_creation,
    validate_batch_for_stock_reduction,
    calculate_semaforo_status,
    is_batch_eligible_for_reservation,
    set_time_provider,
    get_current_date,
    TARJAS_VALIDAS,
)


class TestExpirationValidation:
    """Tests for expiration date validation."""

    def test_valid_future_date(self):
        """A future date should pass validation."""
        future_date = date.today() + timedelta(days=60)
        result = validate_expiration(future_date)
        assert result.is_valid is True
        assert result.error_message is None

    def test_expired_date_yesterday(self):
        """A date in the past should fail validation."""
        past_date = date.today() - timedelta(days=1)
        result = validate_expiration(past_date)
        assert result.is_valid is False
        assert "vencido" in result.error_message.lower()

    def test_expired_date_today(self):
        """Today's date should be considered expired."""
        today = date.today()
        result = validate_expiration(today)
        assert result.is_valid is False
        assert "vencido" in result.error_message.lower()

    def test_none_date(self):
        """None date should fail validation."""
        result = validate_expiration(None)
        assert result.is_valid is False
        assert "obrigatória" in result.error_message.lower()

    def test_expiration_with_frozen_time(self):
        """Expiration validation should respect frozen time provider."""
        # Set frozen time to 2024-01-15
        frozen_date = date(2024, 1, 15)
        set_time_provider(lambda: frozen_date)
        
        try:
            # Date before frozen time should be expired
            past_date = date(2024, 1, 10)
            result = validate_expiration(past_date)
            assert result.is_valid is False
            
            # Date after frozen time should be valid
            future_date = date(2024, 2, 10)
            result = validate_expiration(future_date)
            assert result.is_valid is True
        finally:
            # Reset time provider
            set_time_provider(None)

    def test_expiration_with_custom_reference_date(self):
        """Expiration validation should accept custom reference date."""
        reference = date(2024, 6, 1)
        
        # Date before reference should be expired
        past_date = date(2024, 5, 1)
        result = validate_expiration(past_date, reference_date=reference)
        assert result.is_valid is False
        
        # Date after reference should be valid
        future_date = date(2024, 7, 1)
        result = validate_expiration(future_date, reference_date=reference)
        assert result.is_valid is True


class TestTarjaValidation:
    """Tests for classification (tarja) validation."""

    def test_valid_tarja_sem_tarja(self):
        """'Sem Tarja' should be valid."""
        result = validate_tarja("Sem Tarja")
        assert result.is_valid is True

    def test_valid_tarja_vermelha(self):
        """'Tarja Vermelha' should be valid."""
        result = validate_tarja("Tarja Vermelha")
        assert result.is_valid is True

    def test_valid_tarja_amarela(self):
        """'Tarja Amarela' should be valid."""
        result = validate_tarja("Tarja Amarela")
        assert result.is_valid is True

    def test_valid_tarja_portaria_344(self):
        """'Portaria 344' should be valid."""
        result = validate_tarja("Portaria 344")
        assert result.is_valid is True

    def test_invalid_tarja(self):
        """Unknown tarja should be rejected by default."""
        result = validate_tarja("Invalid Classification")
        assert result.is_valid is False
        assert "inválida" in result.error_message.lower()

    def test_empty_tarja(self):
        """Empty tarja should fail validation."""
        result = validate_tarja("")
        assert result.is_valid is False
        assert "obrigatória" in result.error_message.lower()

    def test_none_tarja(self):
        """None tarja should fail validation."""
        result = validate_tarja(None)
        assert result.is_valid is False
        assert "obrigatória" in result.error_message.lower()

    def test_whitespace_tarja(self):
        """Whitespace-only tarja should fail validation."""
        result = validate_tarja("   ")
        assert result.is_valid is False

    def test_unknown_tarja_with_allow_unknown(self):
        """Unknown tarja should be allowed with warning when allow_unknown=True."""
        result = validate_tarja("Unknown", allow_unknown=True)
        assert result.is_valid is True
        assert len(result.warnings) > 0
        assert "não reconhecida" in result.warnings[0].lower()

    def test_tarja_list_constants(self):
        """TARJAS_VALIDAS should contain all expected values."""
        assert "Sem Tarja" in TARJAS_VALIDAS
        assert "Tarja Amarela" in TARJAS_VALIDAS
        assert "Tarja Vermelha" in TARJAS_VALIDAS
        assert "Portaria 344" in TARJAS_VALIDAS


class TestQuantityValidation:
    """Tests for quantity validation."""

    def test_positive_quantity(self):
        """Positive quantity should be valid."""
        result = validate_quantity(10)
        assert result.is_valid is True

    def test_zero_quantity(self):
        """Zero quantity should fail for creation."""
        result = validate_quantity(0)
        assert result.is_valid is False
        assert "maior que zero" in result.error_message.lower()

    def test_negative_quantity(self):
        """Negative quantity should fail."""
        result = validate_quantity(-5)
        assert result.is_valid is False
        assert "negativa" in result.error_message.lower()

    def test_none_quantity(self):
        """None quantity should fail."""
        result = validate_quantity(None)
        assert result.is_valid is False
        assert "obrigatória" in result.error_message.lower()

    def test_string_quantity(self):
        """String quantity should fail type validation."""
        result = validate_quantity("10")
        assert result.is_valid is False
        assert "inteiro" in result.error_message.lower()

    def test_float_quantity(self):
        """Float quantity should fail type validation."""
        result = validate_quantity(10.5)
        assert result.is_valid is False
        assert "inteiro" in result.error_message.lower()


class TestBatchCreationValidation:
    """Tests for comprehensive batch creation validation."""

    def test_valid_batch(self):
        """A valid batch should pass all validations."""
        result = validate_batch_for_creation(
            nome="Paracetamol 500mg",
            lote="LOT12345",
            data_validade=date.today() + timedelta(days=90),
            quantidade=100,
            tarja="Sem Tarja"
        )
        assert result.is_valid is True
        assert result.error_message is None

    def test_batch_expired(self):
        """An expired batch should fail validation."""
        result = validate_batch_for_creation(
            nome="Paracetamol 500mg",
            lote="LOT12345",
            data_validade=date.today() - timedelta(days=10),
            quantidade=100,
            tarja="Sem Tarja"
        )
        assert result.is_valid is False
        assert "vencido" in result.error_message.lower()

    def test_batch_invalid_tarja(self):
        """Invalid tarja should fail validation."""
        result = validate_batch_for_creation(
            nome="Paracetamol 500mg",
            lote="LOT12345",
            data_validade=date.today() + timedelta(days=90),
            quantidade=100,
            tarja="Invalid Tarja"
        )
        assert result.is_valid is False
        assert "inválida" in result.error_message.lower()

    def test_batch_invalid_quantity(self):
        """Invalid quantity should fail validation."""
        result = validate_batch_for_creation(
            nome="Paracetamol 500mg",
            lote="LOT12345",
            data_validade=date.today() + timedelta(days=90),
            quantidade=-5,
            tarja="Sem Tarja"
        )
        assert result.is_valid is False
        assert "quantidade" in result.error_message.lower()

    def test_batch_missing_name(self):
        """Missing name should fail validation."""
        result = validate_batch_for_creation(
            nome="",
            lote="LOT12345",
            data_validade=date.today() + timedelta(days=90),
            quantidade=100,
            tarja="Sem Tarja"
        )
        assert result.is_valid is False
        assert "nome" in result.error_message.lower()

    def test_batch_missing_lote(self):
        """Missing lote should fail validation."""
        result = validate_batch_for_creation(
            nome="Paracetamol 500mg",
            lote="",
            data_validade=date.today() + timedelta(days=90),
            quantidade=100,
            tarja="Sem Tarja"
        )
        assert result.is_valid is False
        assert "lote" in result.error_message.lower()

    def test_batch_multiple_errors(self):
        """Multiple errors should be reported together."""
        result = validate_batch_for_creation(
            nome="",
            lote="",
            data_validade=date.today() - timedelta(days=10),
            quantidade=-5,
            tarja="Invalid"
        )
        assert result.is_valid is False
        # Should contain multiple error messages
        assert ";" in result.error_message or len(result.error_message) > 50


class TestStockReductionValidation:
    """Tests for stock reduction (baixa) validation."""

    def test_valid_stock_reduction(self):
        """Valid stock reduction should pass."""
        result = validate_batch_for_stock_reduction(
            data_validade=date.today() + timedelta(days=60),
            quantidade_solicitada=10,
            quantidade_disponivel=100
        )
        assert result.is_valid is True

    def test_stock_reduction_expired_batch(self):
        """Cannot reduce stock of expired batch."""
        result = validate_batch_for_stock_reduction(
            data_validade=date.today() - timedelta(days=10),
            quantidade_solicitada=10,
            quantidade_disponivel=100
        )
        assert result.is_valid is False
        assert "vencido" in result.error_message.lower()

    def test_stock_reduction_insufficient_quantity(self):
        """Cannot reduce more than available."""
        result = validate_batch_for_stock_reduction(
            data_validade=date.today() + timedelta(days=60),
            quantidade_solicitada=150,
            quantidade_disponivel=100
        )
        assert result.is_valid is False
        assert "insuficiente" in result.error_message.lower()

    def test_stock_reduction_zero_quantity(self):
        """Cannot reduce zero quantity."""
        result = validate_batch_for_stock_reduction(
            data_validade=date.today() + timedelta(days=60),
            quantidade_solicitada=0,
            quantidade_disponivel=100
        )
        assert result.is_valid is False
        assert "maior que zero" in result.error_message.lower()

    def test_stock_reduction_negative_quantity(self):
        """Cannot reduce negative quantity."""
        result = validate_batch_for_stock_reduction(
            data_validade=date.today() + timedelta(days=60),
            quantidade_solicitada=-5,
            quantidade_disponivel=100
        )
        assert result.is_valid is False


class TestSemaforoStatus:
    """Tests for semaphore status calculation."""

    def test_status_green_safe(self):
        """More than 30 days should be green (0)."""
        future_date = date.today() + timedelta(days=60)
        status = calculate_semaforo_status(future_date)
        assert status == 0

    def test_status_yellow_warning(self):
        """1-30 days should be yellow (1)."""
        future_date = date.today() + timedelta(days=15)
        status = calculate_semaforo_status(future_date)
        assert status == 1

    def test_status_red_expired(self):
        """Today or past should be red (2)."""
        past_date = date.today() - timedelta(days=1)
        status = calculate_semaforo_status(past_date)
        assert status == 2

    def test_status_red_today(self):
        """Today should be red (2)."""
        today = date.today()
        status = calculate_semaforo_status(today)
        assert status == 2

    def test_status_yellow_boundary_30_days(self):
        """Exactly 30 days should be yellow (1)."""
        future_date = date.today() + timedelta(days=30)
        status = calculate_semaforo_status(future_date)
        assert status == 1

    def test_status_green_boundary_31_days(self):
        """31 days should be green (0)."""
        future_date = date.today() + timedelta(days=31)
        status = calculate_semaforo_status(future_date)
        assert status == 0

    def test_status_with_frozen_time(self):
        """Status calculation should respect frozen time."""
        frozen_date = date(2024, 1, 15)
        set_time_provider(lambda: frozen_date)
        
        try:
            # 60 days after frozen time should be green
            future_date = date(2024, 3, 15)
            status = calculate_semaforo_status(future_date)
            assert status == 0
            
            # 10 days after frozen time should be yellow
            near_date = date(2024, 1, 25)
            status = calculate_semaforo_status(near_date)
            assert status == 1
            
            # Before frozen time should be red
            past_date = date(2024, 1, 10)
            status = calculate_semaforo_status(past_date)
            assert status == 2
        finally:
            set_time_provider(None)


class TestEligibilityForReservation:
    """Tests for reservation eligibility."""

    def test_eligible_valid_batch(self):
        """Valid batch should be eligible for reservation."""
        future_date = date.today() + timedelta(days=60)
        eligible = is_batch_eligible_for_reservation(future_date)
        assert eligible is True

    def test_not_eligible_expired_batch(self):
        """Expired batch should not be eligible for reservation."""
        past_date = date.today() - timedelta(days=10)
        eligible = is_batch_eligible_for_reservation(past_date)
        assert eligible is False

    def test_not_eligible_today(self):
        """Batch expiring today should not be eligible."""
        today = date.today()
        eligible = is_batch_eligible_for_reservation(today)
        assert eligible is False

    def test_eligibility_with_frozen_time(self):
        """Eligibility should respect frozen time."""
        frozen_date = date(2024, 6, 1)
        set_time_provider(lambda: frozen_date)
        
        try:
            # After frozen time should be eligible
            future_date = date(2024, 7, 1)
            eligible = is_batch_eligible_for_reservation(future_date)
            assert eligible is True
            
            # Before frozen time should not be eligible
            past_date = date(2024, 5, 1)
            eligible = is_batch_eligible_for_reservation(past_date)
            assert eligible is False
        finally:
            set_time_provider(None)


class TestTimeProvider:
    """Tests for injectable time provider."""

    def test_default_time_provider(self):
        """Default time provider should return current date."""
        current = get_current_date()
        assert isinstance(current, date)
        # Should be close to today (within 1 day for timezone safety)
        assert abs((current - date.today()).days) <= 1

    def test_custom_time_provider(self):
        """Custom time provider should return specified date."""
        custom_date = date(2024, 3, 15)
        set_time_provider(lambda: custom_date)
        
        try:
            current = get_current_date()
            assert current == custom_date
        finally:
            set_time_provider(None)

    def test_reset_time_provider(self):
        """Resetting time provider should restore default behavior."""
        custom_date = date(2024, 3, 15)
        set_time_provider(lambda: custom_date)
        set_time_provider(None)
        
        current = get_current_date()
        assert isinstance(current, date)
        assert abs((current - date.today()).days) <= 1

    def test_datetime_provider_converted_to_date(self):
        """Provider returning datetime should be converted to date."""
        custom_datetime = datetime(2024, 3, 15, 12, 30, 45)
        set_time_provider(lambda: custom_datetime)
        
        try:
            current = get_current_date()
            assert isinstance(current, date)
            assert current == date(2024, 3, 15)
        finally:
            set_time_provider(None)
