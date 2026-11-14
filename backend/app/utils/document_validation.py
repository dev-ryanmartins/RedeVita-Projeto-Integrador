"""
Validação Unificada de Documentos Brasileiros (CPF e CNPJ)

Este módulo fornece validação autoritativa para CPF e CNPJ, suportando:
- CPF com dígitos verificadores
- CNPJ numérico (formato tradicional)
- CNPJ alfanumérico (formato atual com letras A-Z)

Fonte normativa:
- CPF: Receita Federal do Brasil - Regras de cálculo dos dígitos verificadores
- CNPJ: Receita Federal do Brasil - Instruções Normativas SRF nº 95/2002 e atualizações
"""

import re


class DocumentValidationError(Exception):
    """Exceção para erros de validação de documento"""
    pass


def validar_cpf(cpf: str) -> bool:
    """
    Valida CPF brasileiro com dígitos verificadores.
    
    Args:
        cpf: String de CPF (com ou sem formatação)
    
    Returns:
        True se CPF válido, False caso contrário
    
    Critérios de validação:
    - Deve ter 11 dígitos
    - Não pode ser uma sequência repetida (ex: 111.111.111-11)
    - Dígitos verificadores devem estar corretos
    """
    if not isinstance(cpf, str):
        return False
    
    # Remove caracteres não numéricos
    cpf_numeros = re.sub(r'\D', '', cpf)
    
    # Valida tamanho
    if len(cpf_numeros) != 11:
        return False
    
    # Valida sequência repetida
    if cpf_numeros == cpf_numeros[0] * 11:
        return False
    
    # Valida dígito verificador 1
    soma = sum(int(cpf_numeros[i]) * (10 - i) for i in range(9))
    resto = (soma * 10) % 11
    digito1 = 0 if resto == 10 else resto
    
    if int(cpf_numeros[9]) != digito1:
        return False
    
    # Valida dígito verificador 2
    soma = sum(int(cpf_numeros[i]) * (11 - i) for i in range(10))
    resto = (soma * 10) % 11
    digito2 = 0 if resto == 10 else resto
    
    if int(cpf_numeros[10]) != digito2:
        return False
    
    return True


def validar_cnpj(cnpj: str) -> bool:
    """
    Valida CNPJ brasileiro, suportando formatos numérico e alfanumérico.
    
    Args:
        cnpj: String de CNPJ (com ou sem formatação, numérico ou alfanumérico)
    
    Returns:
        True se CNPJ válido, False caso contrário
    
    Formatos suportados:
    - Numérico: 14 dígitos (ex: 12345678000191)
    - Alfanumérico: 12 caracteres (A-Z ou 0-9) + 2 dígitos verificadores (ex: ABC12345678901)
    
    Critérios de validação:
    - Deve ter 14 caracteres (12 base + 2 verificadores)
    - Caracteres base devem ser A-Z ou 0-9
    - Dígitos verificadores devem ser numéricos
    - Não pode ser uma sequência repetida
    - Dígitos verificadores devem estar corretos
    """
    if not isinstance(cnpj, str):
        return False
    
    # Remove separadores comuns (., /, -)
    cnpj_limpo = re.sub(r'[./-]', '', cnpj).upper()
    
    # Valida tamanho
    if len(cnpj_limpo) != 14:
        return False
    
    # Valida sequência repetida
    if cnpj_limpo == cnpj_limpo[0] * 14:
        return False
    
    # Separa base (12 caracteres) e dígitos verificadores (2 caracteres)
    base = cnpj_limpo[:12]
    dv1_str = cnpj_limpo[12]
    dv2_str = cnpj_limpo[13]
    
    # Valida que os DVs são numéricos
    if not (dv1_str.isdigit() and dv2_str.isdigit()):
        return False
    
    dv1 = int(dv1_str)
    dv2 = int(dv2_str)
    
    # Determina se é alfanumérico ou numérico
    eh_alfanumerico = any(c.isalpha() for c in base)
    
    if eh_alfanumerico:
        # Valida formato alfanumérico: apenas A-Z e 0-9 na base
        if not re.match(r'^[A-Z0-9]{12}$', base):
            return False
        
        # Cálculo de DV para CNPJ alfanumérico
        # Converte letras para números (A=10, B=11, ..., Z=35)
        pesos_base = []
        for c in base:
            if c.isdigit():
                pesos_base.append(int(c))
            else:
                pesos_base.append(ord(c) - ord('A') + 10)
        
        # Cálculo do primeiro dígito verificador
        pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma1 = sum(p * w for p, w in zip(pesos_base, pesos1))
        resto1 = soma1 % 11
        dv1_calc = 0 if resto1 < 2 else 11 - resto1
        
        if dv1 != dv1_calc:
            return False
        
        # Cálculo do segundo dígito verificador
        pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        pesos_base_com_dv1 = pesos_base + [dv1]
        soma2 = sum(p * w for p, w in zip(pesos_base_com_dv1, pesos2))
        resto2 = soma2 % 11
        dv2_calc = 0 if resto2 < 2 else 11 - resto2
        
        if dv2 != dv2_calc:
            return False
        
    else:
        # Valida formato numérico: apenas dígitos
        if not base.isdigit():
            return False
        
        # Cálculo de DV para CNPJ numérico (algoritmo tradicional)
        pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma1 = sum(int(c) * w for c, w in zip(base, pesos1))
        resto1 = soma1 % 11
        dv1_calc = 0 if resto1 < 2 else 11 - resto1
        
        if dv1 != dv1_calc:
            return False
        
        pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        base_com_dv1 = base + str(dv1)
        soma2 = sum(int(c) * w for c, w in zip(base_com_dv1, pesos2))
        resto2 = soma2 % 11
        dv2_calc = 0 if resto2 < 2 else 11 - resto2
        
        if dv2 != dv2_calc:
            return False
    
    return True


def normalizar_cpf(cpf: str) -> str:
    """
    Normaliza CPF removendo formatação.
    
    Args:
        cpf: String de CPF (com ou sem formatação)
    
    Returns:
        CPF normalizado (apenas 11 dígitos) ou string vazia se inválido
    """
    if not isinstance(cpf, str):
        return ""
    
    cpf_numeros = re.sub(r'\D', '', cpf)
    
    if len(cpf_numeros) == 11:
        return cpf_numeros
    
    return ""


def normalizar_cnpj(cnpj: str) -> str:
    """
    Normaliza CNPJ preservando letras alfanuméricas.
    
    Args:
        cnpj: String de CNPJ (com ou sem formatação)
    
    Returns:
        CNPJ normalizado (14 caracteres, sem separadores) ou string vazia se inválido
    """
    if not isinstance(cnpj, str):
        return ""
    
    # Remove separadores, mas preserva letras
    cnpj_limpo = re.sub(r'[./-]', '', cnpj).upper()
    
    if len(cnpj_limpo) == 14:
        return cnpj_limpo
    
    return ""


def formatar_cpf(cpf: str) -> str:
    """
    Formata CPF para apresentação (XXX.XXX.XXX-XX).
    
    Args:
        cpf: String de CPF (com ou sem formatação)
    
    Returns:
        CPF formatado ou string original se não for possível formatar
    """
    cpf_normalizado = normalizar_cpf(cpf)
    
    if len(cpf_normalizado) == 11:
        return f"{cpf_normalizado[:3]}.{cpf_normalizado[3:6]}.{cpf_normalizado[6:9]}-{cpf_normalizado[9:]}"
    
    return cpf


def formatar_cnpj(cnpj: str) -> str:
    """
    Formata CNPJ para apresentação (XX.XXX.XXX/YYYY-ZZ).
    
    Args:
        cnpj: String de CNPJ (com ou sem formatação, numérico ou alfanumérico)
    
    Returns:
        CNPJ formatado ou string original se não for possível formatar
    """
    cnpj_normalizado = normalizar_cnpj(cnpj)
    
    if len(cnpj_normalizado) == 14:
        return f"{cnpj_normalizado[:2]}.{cnpj_normalizado[2:5]}.{cnpj_normalizado[5:8]}/{cnpj_normalizado[8:12]}-{cnpj_normalizado[12:]}"
    
    return cnpj
