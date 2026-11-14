"""
Centralized domain validation service for medication batches.

This module provides unified validation and eligibility rules for medication
inventory operations across web and API routes. It ensures consistent
handling of expiration dates, classification (tarja), quantity, and
authorization checks.

Key principles:
- Expired batches are rejected in all operations (creation, triage, stock reduction)
- Unknown/ambiguous classification is never auto-approved; requires manual review
- Time is injectable for testing with frozen clocks
- No external service failures result in automatic approval
- No name heuristics are treated as final clinical decisions
- Stock reduction is atomic to prevent race conditions under concurrency
"""

from datetime import date, datetime
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass


# Injectable time source for testing
_current_time_provider = None


def set_time_provider(provider):
    """
    Set a custom time provider for testing (frozen clock).
    
    Args:
        provider: A callable that returns a date or datetime object.
                  If None, resets to system time.
    """
    global _current_time_provider
    _current_time_provider = provider


def get_current_date() -> date:
    """
    Get the current date from the configured time provider.
    
    Returns:
        Current date as a date object.
    """
    if _current_time_provider:
        result = _current_time_provider()
        if isinstance(result, datetime):
            return result.date()
        return result
    return date.today()


# Valid tarja classifications - defined once as source of truth
TARJAS_VALIDAS = ["Sem Tarja", "Tarja Amarela", "Tarja Vermelha", "Portaria 344"]


@dataclass
class ValidationResult:
    """Result of a validation operation."""
    is_valid: bool
    error_message: Optional[str] = None
    warnings: list = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


def validate_expiration(data_validade: date, reference_date: Optional[date] = None) -> ValidationResult:
    """
    Validate that a medication batch is not expired.
    
    Args:
        data_validade: The expiration date of the batch.
        reference_date: Optional reference date for testing (frozen clock).
                        If None, uses current date from time provider.
    
    Returns:
        ValidationResult indicating if the batch is valid or expired.
    """
    if not data_validade:
        return ValidationResult(False, "Data de validade é obrigatória.")
    
    ref_date = reference_date or get_current_date()
    
    # Check if expired (validity date is today or in the past)
    if data_validade <= ref_date:
        return ValidationResult(
            False,
            f"Lote vencido: data de validade ({data_validade.isoformat()}) "
            f"é anterior ou igual à data de referência ({ref_date.isoformat()})."
        )
    
    return ValidationResult(True)


def validate_tarja(tarja: str, allow_unknown: bool = False) -> ValidationResult:
    """
    Validate medication classification (tarja).
    
    By default, unknown/invalid tarja values are rejected unless explicitly
    allowed. This prevents automatic approval of unverified classifications.
    
    Args:
        tarja: The classification value to validate.
        allow_unknown: If True, allows unknown values (e.g., for manual review).
                       If False (default), rejects unknown values.
    
    Returns:
        ValidationResult with the validated tarja or error.
    """
    if not tarja:
        return ValidationResult(False, "Classificação (tarja) é obrigatória.")
    
    tarja_normalized = tarja.strip()
    
    if tarja_normalized not in TARJAS_VALIDAS:
        if allow_unknown:
            return ValidationResult(
                True,
                warnings=[f"Classificação '{tarja_normalized}' não reconhecida; requer revisão manual."]
            )
        else:
            return ValidationResult(
                False,
                f"Classificação inválida: '{tarja_normalized}'. "
                f"Valores válidos: {', '.join(TARJAS_VALIDAS)}."
            )
    
    return ValidationResult(True)


def validate_quantity(quantidade: int) -> ValidationResult:
    """
    Validate medication quantity.
    
    Args:
        quantidade: The quantity to validate.
    
    Returns:
        ValidationResult indicating if the quantity is valid.
    """
    if quantidade is None:
        return ValidationResult(False, "Quantidade é obrigatória.")
    
    if not isinstance(quantidade, int):
        return ValidationResult(False, "Quantidade deve ser um número inteiro.")
    
    if quantidade < 0:
        return ValidationResult(False, "Quantidade não pode ser negativa.")
    
    if quantidade == 0:
        return ValidationResult(False, "Quantidade deve ser maior que zero para cadastro.")
    
    return ValidationResult(True)


def validate_batch_for_creation(
    nome: str,
    lote: str,
    data_validade: date,
    quantidade: int,
    tarja: str,
    reference_date: Optional[date] = None
) -> ValidationResult:
    """
    Comprehensive validation for creating a new medication batch.
    
    This combines all validation rules for inventory creation and triage.
    Expired batches are always rejected. Unknown classifications are rejected
    unless explicitly configured otherwise.
    
    Args:
        nome: Medication name.
        lote: Batch number.
        data_validade: Expiration date.
        quantidade: Quantity.
        tarja: Classification.
        reference_date: Optional reference date for testing.
    
    Returns:
        ValidationResult with combined validation results.
    """
    errors = []
    warnings = []
    
    # Basic field presence
    if not nome or not nome.strip():
        errors.append("Nome do medicamento é obrigatório.")
    
    if not lote or not lote.strip():
        errors.append("Número do lote é obrigatório.")
    
    # Expiration validation - critical safety check
    exp_result = validate_expiration(data_validade, reference_date)
    if not exp_result.is_valid:
        errors.append(exp_result.error_message)
    
    # Quantity validation
    qty_result = validate_quantity(quantidade)
    if not qty_result.is_valid:
        errors.append(qty_result.error_message)
    
    # Tarja validation - reject unknown classifications
    tarja_result = validate_tarja(tarja, allow_unknown=False)
    if not tarja_result.is_valid:
        errors.append(tarja_result.error_message)
    elif tarja_result.warnings:
        warnings.extend(tarja_result.warnings)
    
    if errors:
        return ValidationResult(False, "; ".join(errors), warnings)
    
    return ValidationResult(True, warnings=warnings)


def validate_batch_for_stock_reduction(
    data_validade: date,
    quantidade_solicitada: int,
    quantidade_disponivel: int,
    reference_date: Optional[date] = None
) -> ValidationResult:
    """
    Validate that a batch can be reduced in stock (baixa/dispensação).
    
    Revalidates expiration at operation time, not just at creation.
    Ensures sufficient quantity is available.
    
    Args:
        data_validade: Expiration date of the batch.
        quantidade_solicitada: Quantity to reduce.
        quantidade_disponivel: Current available quantity.
        reference_date: Optional reference date for testing.
    
    Returns:
        ValidationResult indicating if the operation is allowed.
    """
    errors = []
    
    # Revalidate expiration at operation time
    exp_result = validate_expiration(data_validade, reference_date)
    if not exp_result.is_valid:
        errors.append(exp_result.error_message)
    
    # Validate quantity
    if quantidade_solicitada <= 0:
        errors.append("Quantidade solicitada deve ser maior que zero.")
    
    if quantidade_solicitada > quantidade_disponivel:
        errors.append(
            f"Estoque insuficiente: solicitado {quantidade_solicitada}, "
            f"disponível {quantidade_disponivel}."
        )
    
    if errors:
        return ValidationResult(False, "; ".join(errors))
    
    return ValidationResult(True)


def calculate_semaforo_status(data_validade: date, reference_date: Optional[date] = None) -> int:
    """
    Calculate semaphore status based on expiration date.
    
    Status codes:
    - 0: Green (safe, > 30 days until expiration)
    - 1: Yellow (warning, 1-30 days until expiration)
    - 2: Red (expired or expiring today)
    
    Args:
        data_validade: Expiration date.
        reference_date: Optional reference date for testing.
    
    Returns:
        Integer status code (0, 1, or 2).
    """
    ref_date = reference_date or get_current_date()
    dias_restantes = (data_validade - ref_date).days
    
    if dias_restantes <= 0:
        return 2  # Vencido
    elif dias_restantes <= 30:
        return 1  # Alerta (menos de um mês)
    else:
        return 0  # Seguro


def atomic_reduce_stock_quantity(
    db_session,
    medicamento_id: int,
    quantidade_solicitada: int
) -> Tuple[bool, int]:
    """
    Atomically reduce stock quantity using conditional UPDATE.
    
    This function performs an atomic stock reduction by using a conditional
    UPDATE statement that checks the current quantity in the WHERE clause.
    If the condition is not met (insufficient stock), no rows are updated.
    
    This approach works across SQLite, MySQL, and PostgreSQL and prevents
    race conditions where concurrent requests could approve withdrawals
    exceeding the available balance.
    
    Args:
        db_session: SQLAlchemy session.
        medicamento_id: ID of the medication batch.
        quantidade_solicitada: Quantity to reduce.
    
    Returns:
        Tuple of (success, new_quantity):
        - success: True if reduction succeeded, False if insufficient stock.
        - new_quantity: The new quantity after reduction (only valid if success=True).
    
    Example:
        success, new_qty = atomic_reduce_stock_quantity(db.session, med_id, 5)
        if success:
            print(f"Reduced to {new_qty}")
        else:
            print("Insufficient stock")
    """
    from sqlalchemy import text
    
    # Conditional UPDATE: only succeeds if current quantity >= requested quantity
    # This is atomic at the database level
    update_stmt = text("""
        UPDATE medicamentos
        SET quantidade = quantidade - :quantidade_solicitada
        WHERE id = :medicamento_id
          AND quantidade >= :quantidade_solicitada
    """)
    
    result = db_session.execute(
        update_stmt,
        {
            "medicamento_id": medicamento_id,
            "quantidade_solicitada": quantidade_solicitada
        }
    )
    
    # Check if any row was updated
    rows_affected = result.rowcount
    
    if rows_affected == 0:
        # No row updated means condition failed (insufficient stock)
        return False, 0
    
    # Fetch the new quantity to return
    select_stmt = text("SELECT quantidade FROM medicamentos WHERE id = :medicamento_id")
    new_qty_result = db_session.execute(
        select_stmt,
        {"medicamento_id": medicamento_id}
    ).fetchone()
    
    new_quantity = new_qty_result[0] if new_qty_result else 0
    
    return True, new_quantity


def is_batch_eligible_for_reservation(data_validade: date, reference_date: Optional[date] = None) -> bool:
    """
    Determine if a batch is eligible for reservation/dispensing.
    
    A batch is eligible only if it is not expired.
    
    Args:
        data_validade: Expiration date.
        reference_date: Optional reference date for testing.
    
    Returns:
        True if eligible, False if expired.
    """
    exp_result = validate_expiration(data_validade, reference_date)
    return exp_result.is_valid
