from datetime import date

def calcular_status_semaforo(data_validade):
    # Regra: Verde (0), Amarelo < 30 dias (1), Vermelho Vencido (2)
    hoje = date.today()
    dias_restantes = (data_validade - hoje).days

    if dias_restantes < 0:
        return 2  # Vencido
    elif dias_restantes <= 30:
        return 1  # Alerta (menos de um mês)
    else:
        return 0  # Seguro