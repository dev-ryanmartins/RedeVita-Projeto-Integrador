from werkzeug.security import generate_password_hash, check_password_hash
import re

METODO_HASH = "scrypt"


def criptografar_senha(senha):
    """
    Criptografa senha usando scrypt (método seguro do werkzeug).
    Scrypt é resistente a ataques de força bruta e hardware dedicado.
    """
    if not senha or len(senha) < 8:
        raise ValueError("Senha deve ter no mínimo 8 caracteres")
    return generate_password_hash(senha, method=METODO_HASH)


def verificar_senha(senha_hash, senha_plana):
    """
    Verifica se a senha em texto plano corresponde ao hash armazenado.
    """
    if not senha_hash or not senha_plana:
        return False
    return check_password_hash(senha_hash, senha_plana)


def validar_forca_senha(senha):
    """
    Valida a força da senha conforme políticas de segurança.
    Retorna tuple (valida, mensagem).
    """
    if len(senha) < 8:
        return False, "Senha deve ter no mínimo 8 caracteres"
    
    if len(senha) > 128:
        return False, "Senha muito longa (máximo 128 caracteres)"
    
    # Verifica se contém pelo menos uma letra maiúscula
    if not re.search(r'[A-Z]', senha):
        return False, "Senha deve conter pelo menos uma letra maiúscula"
    
    # Verifica se contém pelo menos uma letra minúscula
    if not re.search(r'[a-z]', senha):
        return False, "Senha deve conter pelo menos uma letra minúscula"
    
    # Verifica se contém pelo menos um número
    if not re.search(r'\d', senha):
        return False, "Senha deve conter pelo menos um número"
    
    # Verifica se contém pelo menos um caractere especial
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', senha):
        return False, "Senha deve conter pelo menos um caractere especial"
    
    return True, "Senha válida"
