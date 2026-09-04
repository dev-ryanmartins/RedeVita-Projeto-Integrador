from werkzeug.security import generate_password_hash, check_password_hash

METODO_HASH = "scrypt"


def criptografar_senha(senha):
    return generate_password_hash(senha, method=METODO_HASH)


def verificar_senha(senha_hash, senha_plana):
    return check_password_hash(senha_hash, senha_plana)
