import re
import html as _html

_CTRL_RE = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]')


def limpar(value: str, max_len: int = 255) -> str:
    if not isinstance(value, str):
        return ''
    value = _CTRL_RE.sub('', value).strip()
    return value[:max_len]


def limpar_html(value: str, max_len: int = 255) -> str:
    return _html.escape(limpar(value, max_len))


def limpar_inteiro(value, default: int = 0, minimo: int = None, maximo: int = None) -> int:
    try:
        v = int(str(value).strip())
    except (ValueError, TypeError):
        return default
    if minimo is not None and v < minimo:
        return minimo
    if maximo is not None and v > maximo:
        return maximo
    return v


def validar_cpf_digitos(cpf: str) -> bool:
    cpf = re.sub(r'\D', '', cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for i in range(2):
        soma = sum(int(cpf[j]) * (10 + i - j) for j in range(9 + i))
        resto = (soma * 10) % 11
        if resto == 10:
            resto = 0
        if int(cpf[9 + i]) != resto:
            return False
    return True
