import re
import html as _html
import json
from typing import Any, Dict, List, Union

_CTRL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")
# Padrão para detectar tags HTML e scripts maliciosos
_XSS_PATTERN = re.compile(
    r'<script[^>]*>.*?</script>|'
    r'<iframe[^>]*>.*?</iframe>|'
    r'<object[^>]*>.*?</object>|'
    r'<embed[^>]*>|'
    r'on\w+\s*=|'
    r'javascript:|'
    r'data:text/html',
    re.IGNORECASE
)


def limpar(value: str, max_len: int = 255) -> str:
    if not isinstance(value, str):
        return ""
    value = _CTRL_RE.sub("", value).strip()
    return value[:max_len]


def limpar_html(value: str, max_len: int = 255) -> str:
    return _html.escape(limpar(value, max_len))


def limpar_inteiro(
    value, default: int = 0, minimo: int = None, maximo: int = None
) -> int:
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
    cpf = re.sub(r"\D", "", cpf)
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


def sanitizar_json_payload(payload: Union[Dict, List, str, Any]) -> Union[Dict, List, str]:
    """
    Sanitiza payloads JSON de entrada para prevenir ataques XSS.
    Remove tags HTML, scripts maliciosos e caracteres de controle.
    
    Args:
        payload: Dados JSON (dict, list, string ou outro tipo)
    
    Returns:
        Payload sanitizado com o mesmo tipo de estrutura
    """
    if isinstance(payload, str):
        return limpar_html(payload)
    
    elif isinstance(payload, dict):
        return {key: sanitizar_json_payload(value) for key, value in payload.items()}
    
    elif isinstance(payload, list):
        return [sanitizar_json_payload(item) for item in payload]
    
    elif isinstance(payload, (int, float, bool, type(None))):
        return payload
    
    else:
        # Para outros tipos, converte para string e sanitiza
        return limpar_html(str(payload))


def validar_json_string(json_str: str) -> tuple[bool, Any]:
    """
    Valida e parseia uma string JSON.
    
    Args:
        json_str: String JSON para validar
    
    Returns:
        Tuple (valido, dados_parseados ou mensagem_erro)
    """
    try:
        dados = json.loads(json_str)
        return True, dados
    except json.JSONDecodeError as e:
        return False, f"JSON inválido: {str(e)}"
    except Exception as e:
        return False, f"Erro ao parsear JSON: {str(e)}"


def detectar_xss(value: str) -> bool:
    """
    Detecta padrões de XSS em uma string.
    
    Args:
        value: String para verificar
    
    Returns:
        True se detectar padrões XSS, False caso contrário
    """
    if not isinstance(value, str):
        return False
    return bool(_XSS_PATTERN.search(value))


def sanitizar_input_usuario(value: str, max_len: int = 255, permitir_html: bool = False) -> str:
    """
    Sanitização estrita de input de usuário.
    
    Args:
        value: String de input do usuário
        max_len: Comprimento máximo permitido
        permitir_html: Se False, remove todos os tags HTML
    
    Returns:
        String sanitizada
    """
    if not isinstance(value, str):
        return ""
    
    # Remove caracteres de controle
    value = _CTRL_RE.sub("", value)
    
    # Remove espaços excessivos
    value = " ".join(value.split())
    
    # Detecta XSS
    if detectar_xss(value):
        # Remove tags HTML se detectar XSS
        value = re.sub(r'<[^>]+>', '', value)
    
    # Escapa HTML se não permitido
    if not permitir_html:
        value = _html.escape(value)
    
    # Trunca se necessário
    return value[:max_len].strip()


def validar_email(email: str) -> bool:
    """
    Valida formato de email com regex estrita.
    
    Args:
        email: String de email para validar
    
    Returns:
        True se formato válido, False caso contrário
    """
    if not isinstance(email, str):
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip()))


def validar_telefone(telefone: str) -> str:
    """
    Valida e normaliza número de telefone brasileiro.
    
    Args:
        telefone: String de telefone
    
    Returns:
        Telefone normalizado (apenas dígitos) ou string vazia se inválido
    """
    if not isinstance(telefone, str):
        return ""
    
    # Remove tudo que não é dígito
    digitos = re.sub(r'\D', '', telefone)
    
    # Valida tamanho (10 ou 11 dígitos para Brasil)
    if len(digitos) in [10, 11]:
        return digitos
    
    return ""


def sanitizar_cnpj(cnpj: str) -> str:
    """
    Sanitiza e valida formato básico de CNPJ.
    
    Args:
        cnpj: String de CNPJ
    
    Returns:
        CNPJ sanitizado (apenas dígitos) ou string vazia se inválido
    """
    if not isinstance(cnpj, str):
        return ""
    
    # Remove tudo que não é dígito
    digitos = re.sub(r'\D', '', cnpj)
    
    # Valida tamanho (14 dígitos)
    if len(digitos) == 14:
        return digitos
    
    return ""
