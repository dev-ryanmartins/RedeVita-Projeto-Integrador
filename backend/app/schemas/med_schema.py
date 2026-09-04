from datetime import datetime


def validar_entrada_medicamento(data):
    """Valida os dados de um medicamento antes de salvar no banco."""
    erros = []

    campos = ["nome", "lote", "data_validade", "quantidade"]
    for campo in campos:
        if campo not in data or not data[campo]:
            erros.append(f"O campo '{campo}' não pode estar vazio.")

    # Tenta validar o formato da data (esperado: AAAA-MM-DD)
    if "data_validade" in data and data["data_validade"]:
        try:
            datetime.strptime(data["data_validade"], "%Y-%m-%d")
        except ValueError:
            erros.append("Formato de data inválido. Use AAAA-MM-DD.")

    # Garante que a quantidade seja um número positivo
    if "quantidade" in data:
        try:
            qtd = int(data["quantidade"])
            if qtd < 0:
                erros.append("A quantidade não pode ser negativa.")
        except ValueError:
            erros.append("A quantidade deve ser um número inteiro.")

    if erros:
        return False, erros

    return True, None
