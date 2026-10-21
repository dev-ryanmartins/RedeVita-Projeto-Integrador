from app.utils.medication_validation import get_current_date


def calcular_status_semaforo(data_validade):
    """
    Calculate semaphore status based on expiration date.
    
    Uses the injectable time provider for consistent testing.
    
    Status codes:
    - 0: Green (safe, > 30 days until expiration)
    - 1: Yellow (warning, 1-30 days until expiration)
    - 2: Red (expired or expiring today)
    
    Args:
        data_validade: Expiration date.
    
    Returns:
        Integer status code (0, 1, or 2).
    """
    hoje = get_current_date()
    dias_restantes = (data_validade - hoje).days

    if dias_restantes <= 0:
        return 2  # Vencido
    elif dias_restantes <= 30:
        return 1  # Alerta (menos de um mês)
    else:
        return 0  # Seguro
