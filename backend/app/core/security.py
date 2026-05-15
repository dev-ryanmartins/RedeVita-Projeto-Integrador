from werkzeug.security import generate_password_hash, check_password_hash

def criptografar_senha(senha):
    """Transforma a senha em um código impossível de ler."""
    return generate_password_hash(senha)

def verificar_senha(senha_hash, senha_plana):
    """Compara a senha digitada com o código salvo no banco."""
    return check_password_hash(senha_hash, senha_plana)