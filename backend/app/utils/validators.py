import re
import html
from urllib.parse import quote, unquote


def validar_cpf(cpf):
    cpf = re.sub(r"\D", "", cpf)

    if len(cpf) != 11:
        return False

    if cpf == cpf[0] * 11:
        return False

    return True


def sanitizar_input_string(input_str, max_length=255):
    if not input_str:
        return ""

    if not isinstance(input_str, str):
        input_str = str(input_str)

    input_str = input_str.strip()

    if len(input_str) > max_length:
        input_str = input_str[:max_length]

    input_str = html.escape(input_str, quote=True)
    dangerous_chars = ["'", '"', ";", "--", "/*", "*/", "xp_", "exec"]
    for char in dangerous_chars:
        input_str = input_str.replace(char, "")
    
    return input_str


def validar_email(email):
    if not email or not isinstance(email, str):
        return False

    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email.strip()) is not None


def validar_telefone(telefone):
    if not telefone:
        return True

    telefone = re.sub(r"\D", "", telefone)

    return len(telefone) in [10, 11]


def validar_nome(nome, min_length=2, max_length=100):
    if not nome or not isinstance(nome, str):
        return False

    nome = nome.strip()

    if len(nome) < min_length or len(nome) > max_length:
        return False

    nome_pattern = r'^[a-zA-ZÀ-ÿ\s\-\'\.]+$'
    return re.match(nome_pattern, nome) is not None


def validar_cnpj(cnpj):
    if not cnpj:
        return True

    cnpj = re.sub(r"\D", "", cnpj)

    if len(cnpj) != 14:
        return False

    if cnpj == cnpj[0] * 14:
        return False

    return True


def validar_quantidade(valor, min_val=0, max_val=10000):
    try:
        valor_num = float(valor)
        return min_val <= valor_num <= max_val
    except (ValueError, TypeError):
        return False


def sanitizar_dados_formulario(dados, campos_obrigatorios=None, regras_validacao=None):
    dados_sanitizados = {}
    erros = {}

    if campos_obrigatorios is None:
        campos_obrigatorios = []

    if regras_validacao is None:
        regras_validacao = {}

    for campo, valor in dados.items():
        if isinstance(valor, str):
            dados_sanitizados[campo] = sanitizar_input_string(valor)
        else:
            dados_sanitizados[campo] = valor

    for campo in campos_obrigatorios:
        if campo not in dados_sanitizados or not dados_sanitizados[campo]:
            erros[campo] = f"Campo '{campo}' é obrigatório"

    for campo, regra in regras_validacao.items():
        if campo in dados_sanitizados and dados_sanitizados[campo]:
            if regra == 'email' and not validar_email(dados_sanitizados[campo]):
                erros[campo] = f"Email inválido"
            elif regra == 'cpf' and not validar_cpf(dados_sanitizados[campo]):
                erros[campo] = f"CPF inválido"
            elif regra == 'cnpj' and not validar_cnpj(dados_sanitizados[campo]):
                erros[campo] = f"CNPJ inválido"
            elif regra == 'telefone' and not validar_telefone(dados_sanitizados[campo]):
                erros[campo] = f"Telefone inválido"

    return dados_sanitizados, erros


def detectar_padroes_suspeitos(input_str):
    if not input_str or not isinstance(input_str, str):
        return False

    padroes_suspeitos = [
        r'<script.*?>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'union.*select',
        r'or.*1.*=.*1',
        r'drop.*table',
        r'--.*$',
        r'/\*.*\*/',
        r'\.\./',
        r'eval\(',
        r'exec\(',
    ]

    input_str_lower = input_str.lower()

    for padrao in padroes_suspeitos:
        if re.search(padrao, input_str_lower, re.IGNORECASE):
            return True

    return False
