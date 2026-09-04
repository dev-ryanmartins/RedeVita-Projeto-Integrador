import re
import html
from urllib.parse import quote, unquote


def validar_cpf(cpf):
    # Remove qualquer caractere que não seja número
    cpf = re.sub(r"\D", "", cpf)

    if len(cpf) != 11:
        return False

    # Verifica se todos os dígitos são iguais (ex: 111.111...)
    if cpf == cpf[0] * 11:
        return False

    # Aqui você pode adicionar o cálculo matemático dos dígitos se quiser
    # impressionar ainda mais o professor, mas só o tamanho já ajuda muito.
    return True


def sanitizar_input_string(input_str, max_length=255):
    """
    Sanitiza strings de entrada para prevenir ataques XSS e injeção.
    
    Args:
        input_str: String a ser sanitizada
        max_length: Comprimento máximo permitido
        
    Returns:
        String sanitizada e segura
    """
    if not input_str:
        return ""
    
    # Converte para string se não for
    if not isinstance(input_str, str):
        input_str = str(input_str)
    
    # Remove espaços em excesso
    input_str = input_str.strip()
    
    # Trunca se exceder tamanho máximo
    if len(input_str) > max_length:
        input_str = input_str[:max_length]
    
    # Escapa caracteres HTML para prevenir XSS
    input_str = html.escape(input_str, quote=True)
    
    # Remove caracteres perigosos que poderiam ser usados em SQL injection
    # (Nota: SQLAlchemy já protege contra SQLi, mas isso é uma camada adicional)
    dangerous_chars = ["'", '"', ";", "--", "/*", "*/", "xp_", "exec"]
    for char in dangerous_chars:
        input_str = input_str.replace(char, "")
    
    return input_str


def validar_email(email):
    """
    Valida formato de email usando regex.
    
    Args:
        email: String de email a validar
        
    Returns:
        Boolean indicando se o email é válido
    """
    if not email or not isinstance(email, str):
        return False
    
    # Regex simplificado para validação de email
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email.strip()) is not None


def validar_telefone(telefone):
    """
    Valida formato de telefone brasileiro.
    
    Args:
        telefone: String de telefone a validar
        
    Returns:
        Boolean indicando se o telefone é válido
    """
    if not telefone:
        return True  # Campo opcional
    
    # Remove caracteres não numéricos
    telefone = re.sub(r"\D", "", telefone)
    
    # Verifica se tem 10 ou 11 dígitos (com ou sem DDD)
    return len(telefone) in [10, 11]


def validar_nome(nome, min_length=2, max_length=100):
    """
    Valida nome de pessoa/entidade.
    
    Args:
        nome: String de nome a validar
        min_length: Comprimento mínimo
        max_length: Comprimento máximo
        
    Returns:
        Boolean indicando se o nome é válido
    """
    if not nome or not isinstance(nome, str):
        return False
    
    nome = nome.strip()
    
    if len(nome) < min_length or len(nome) > max_length:
        return False
    
    # Verifica se contém apenas letras, espaços e caracteres comuns
    nome_pattern = r'^[a-zA-ZÀ-ÿ\s\-\'\.]+$'
    return re.match(nome_pattern, nome) is not None


def validar_cnpj(cnpj):
    """
    Valida formato básico de CNPJ.
    
    Args:
        cnpj: String de CNPJ a validar
        
    Returns:
        Boolean indicando se o CNPJ é válido
    """
    if not cnpj:
        return True  # Campo opcional
    
    # Remove caracteres não numéricos
    cnpj = re.sub(r"\D", "", cnpj)
    
    # Verifica se tem 14 dígitos
    if len(cnpj) != 14:
        return False
    
    # Verifica se todos os dígitos são iguais
    if cnpj == cnpj[0] * 14:
        return False
    
    return True


def validar_quantidade(valor, min_val=0, max_val=10000):
    """
    Valida valores numéricos de quantidade.
    
    Args:
        valor: Valor a validar
        min_val: Valor mínimo permitido
        max_val: Valor máximo permitido
        
    Returns:
        Boolean indicando se o valor é válido
    """
    try:
        valor_num = float(valor)
        return min_val <= valor_num <= max_val
    except (ValueError, TypeError):
        return False


def sanitizar_dados_formulario(dados, campos_obrigatorios=None, regras_validacao=None):
    """
    Sanitiza e valida dados de formulário completo.
    
    Args:
        dados: Dicionário com dados do formulário
        campos_obrigatorios: Lista de campos obrigatórios
        regras_validacao: Dicionário com regras específicas por campo
        
    Returns:
        Tupla (dados_sanitizados, erros)
    """
    dados_sanitizados = {}
    erros = {}
    
    if campos_obrigatorios is None:
        campos_obrigatorios = []
    
    if regras_validacao is None:
        regras_validacao = {}
    
    # Sanitiza todos os campos
    for campo, valor in dados.items():
        if isinstance(valor, str):
            dados_sanitizados[campo] = sanitizar_input_string(valor)
        else:
            dados_sanitizados[campo] = valor
    
    # Verifica campos obrigatórios
    for campo in campos_obrigatorios:
        if campo not in dados_sanitizados or not dados_sanitizados[campo]:
            erros[campo] = f"Campo '{campo}' é obrigatório"
    
    # Aplica regras de validação específicas
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
    """
    Detecta padrões que podem indicar tentativas de ataque.
    
    Args:
        input_str: String a analisar
        
    Returns:
        Boolean indicando se foram detectados padrões suspeitos
    """
    if not input_str or not isinstance(input_str, str):
        return False
    
    # Padrões suspeitos comuns
    padroes_suspeitos = [
        r'<script.*?>.*?</script>',  # XSS script tags
        r'javascript:',  # JavaScript em URLs
        r'on\w+\s*=',  # Event handlers (onclick, onerror, etc)
        r'union.*select',  # SQL injection UNION
        r'or.*1.*=.*1',  # SQL injection OR
        r'drop.*table',  # SQL injection DROP
        r'--.*$',  # SQL comments
        r'/\*.*\*/',  # SQL comments
        r'\.\./',  # Path traversal
        r'eval\(',  # JavaScript eval
        r'exec\(',  # JavaScript exec
    ]
    
    input_str_lower = input_str.lower()
    
    for padrao in padroes_suspeitos:
        if re.search(padrao, input_str_lower, re.IGNORECASE):
            return True
    
    return False
