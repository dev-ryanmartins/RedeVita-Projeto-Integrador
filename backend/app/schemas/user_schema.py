from app.utils.validators import validar_cpf

def validar_cadastro_usuario(data):
    """Valida os dados para criação de um novo usuário."""
    erros = []
    
    # Verifica campos obrigatórios
    campos_obrigatorios = ['nome', 'cpf', 'senha']
    for campo in campos_obrigatorios:
        if campo not in data or not data[campo]:
            erros.append(f"O campo '{campo}' é obrigatório.")
    
    # Se já houver erros de campo vazio, para por aqui
    if erros:
        return False, erros

    # Validação específica de CPF (usando sua utilidade de validação)
    if not validar_cpf(data['cpf']):
        erros.append("CPF inválido. Certifique-se de digitar apenas números.")

    # Validação de tamanho de senha
    if len(data['senha']) < 6:
        erros.append("A senha deve ter pelo menos 6 caracteres.")

    if erros:
        return False, erros
    
    return True, None