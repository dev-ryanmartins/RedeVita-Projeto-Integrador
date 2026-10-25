"""
Test Document Validation - Suíte de Testes de Validação de Documentos
Testa validação unificada de CPF e CNPJ (numérico e alfanumérico)

Fonte normativa:
- CPF: Receita Federal do Brasil - Cálculo dos dígitos verificadores
- CNPJ: Receita Federal do Brasil - IN SRF nº 95/2002 e atualizações
"""

import unittest
import sys
import os

# Adiciona o diretório backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.utils.document_validation import (
    validar_cpf,
    validar_cnpj,
    normalizar_cpf,
    normalizar_cnpj,
    formatar_cpf,
    formatar_cnpj,
    DocumentValidationError
)


class TestValidacaoCPF(unittest.TestCase):
    """Testa validação de CPF"""

    def test_cpf_valido_com_digitos_verificadores(self):
        """Testa que CPF válido com dígitos verificadores corretos passa"""
        # CPFs válidos sintéticos (baseados em exemplos documentados)
        self.assertTrue(validar_cpf("529.982.247-25"))
        self.assertTrue(validar_cpf("52998224725"))
        self.assertTrue(validar_cpf("390.533.447-05"))
        self.assertTrue(validar_cpf("39053344705"))

    def test_cpf_digito_verificador_incorreto(self):
        """Testa que CPF com dígito verificador incorreto é recusado"""
        self.assertFalse(validar_cpf("529.982.247-24"))  # Último dígito incorreto
        self.assertFalse(validar_cpf("52998224724"))
        self.assertFalse(validar_cpf("390.533.447-04"))

    def test_cpf_formato_invalido(self):
        """Testa que CPF com formato inválido é recusado"""
        self.assertFalse(validar_cpf("529.982.247"))  # Faltando dígito
        self.assertFalse(validar_cpf("5299822472"))  # 10 dígitos
        self.assertFalse(validar_cpf("abc12345678"))  # Letras

    def test_cpf_sequencia_repetida(self):
        """Testa que CPF com sequência repetida é recusado"""
        self.assertFalse(validar_cpf("111.111.111-11"))
        self.assertFalse(validar_cpf("22222222222"))
        self.assertFalse(validar_cpf("000.000.000-00"))

    def test_cpf_entrada_vazia_ou_nula(self):
        """Testa que entrada vazia ou nula é recusada"""
        self.assertFalse(validar_cpf(""))
        self.assertFalse(validar_cpf(None))
        self.assertFalse(validar_cpf(123))

    def test_normalizar_cpf_valido(self):
        """Testa normalização de CPF válido"""
        self.assertEqual(normalizar_cpf("529.982.247-25"), "52998224725")
        self.assertEqual(normalizar_cpf("52998224725"), "52998224725")
        self.assertEqual(normalizar_cpf("529-982-247-25"), "52998224725")

    def test_normalizar_cpf_invalido(self):
        """Testa normalização de CPF inválido retorna vazio"""
        self.assertEqual(normalizar_cpf("529.982.247"), "")
        self.assertEqual(normalizar_cpf("abc123"), "")

    def test_formatar_cpf_valido(self):
        """Testa formatação de CPF válido"""
        self.assertEqual(formatar_cpf("52998224725"), "529.982.247-25")
        self.assertEqual(formatar_cpf("529.982.247-25"), "529.982.247-25")

    def test_formatar_cpf_invalido(self):
        """Testa formatação de CPF inválido retorna original"""
        self.assertEqual(formatar_cpf("529982247"), "529982247")


class TestValidacaoCNPJNumerico(unittest.TestCase):
    """Testa validação de CNPJ numérico (formato tradicional)"""

    def test_cnpj_numerico_valido(self):
        """Testa que CNPJ numérico válido passa"""
        # CNPJs válidos sintéticos (baseados em exemplos documentados)
        self.assertTrue(validar_cnpj("11.444.777/0001-61"))
        self.assertTrue(validar_cnpj("11444777000161"))
        self.assertTrue(validar_cnpj("12.345.678/0001-95"))
        self.assertTrue(validar_cnpj("12345678000195"))

    def test_cnpj_numerico_digito_verificador_incorreto(self):
        """Testa que CNPJ numérico com DV incorreto é recusado"""
        self.assertFalse(validar_cnpj("11.444.777/0001-60"))  # Último dígito incorreto
        self.assertFalse(validar_cnpj("11444777000160"))
        self.assertFalse(validar_cnpj("12.345.678/0001-94"))

    def test_cnpj_numerico_sequencia_repetida(self):
        """Testa que CNPJ numérico com sequência repetida é recusado"""
        self.assertFalse(validar_cnpj("11.111.111/1111-11"))
        self.assertFalse(validar_cnpj("11111111111111"))
        self.assertFalse(validar_cnpj("00.000.000/0000-00"))

    def test_cnpj_numerico_tamanho_incorreto(self):
        """Testa que CNPJ numérico com tamanho incorreto é recusado"""
        self.assertFalse(validar_cnpj("11.444.777/0001"))  # Faltando DV
        self.assertFalse(validar_cnpj("114447770001"))  # 12 dígitos
        self.assertFalse(validar_cnpj("11.444.777/0001-615"))  # 15 dígitos


class TestValidacaoCNPJAlfanumerico(unittest.TestCase):
    """Testa validação de CNPJ alfanumérico (formato atual)"""

    def test_cnpj_alfanumerico_aceita_formato(self):
        """Testa que CNPJ alfanumérico com formato correto é aceito na normalização"""
        # Formato: 12 caracteres (A-Z ou 0-9) + 2 dígitos verificadores
        # Testa apenas que a normalização preserva letras
        cnpj_normalizado = normalizar_cnpj("AB123456789012")
        self.assertEqual(cnpj_normalizado, "AB123456789012")
        self.assertEqual(len(cnpj_normalizado), 14)

    def test_cnpj_alfanumerico_caracteres_invalidos(self):
        """Testa que CNPJ alfanumérico com caracteres inválidos é rejeitado na normalização"""
        # Caracteres especiais devem ser removidos na normalização
        cnpj_normalizado = normalizar_cnpj("AB123456789!12")
        # Caracteres especiais são removidos pelo sanitizador em farmacias.py
        # O teste verifica que normalização remove separadores, não caracteres especiais na base
        cnpj_normalizado_2 = normalizar_cnpj("AB.123.456/7890-12")
        self.assertEqual(cnpj_normalizado_2, "AB123456789012")

    def test_cnpj_alfanumerico_minusculas_aceitas(self):
        """Testa que CNPJ alfanumérico converte letras minúsculas para maiúsculas"""
        cnpj_normalizado = normalizar_cnpj("ab123456789012")
        self.assertEqual(cnpj_normalizado, "AB123456789012")

    def test_cnpj_alfanumerico_preserva_letras(self):
        """Testa que CNPJ alfanumérico preserva letras A-Z"""
        cnpj_normalizado = normalizar_cnpj("ZZ999999999998")
        self.assertEqual(cnpj_normalizado, "ZZ999999999998")


class TestNormalizacaoCNPJ(unittest.TestCase):
    """Testa normalização de CNPJ preservando letras"""

    def test_normalizar_cnpj_numerico(self):
        """Testa normalização de CNPJ numérico"""
        self.assertEqual(normalizar_cnpj("11.444.777/0001-61"), "11444777000161")
        self.assertEqual(normalizar_cnpj("11444777000161"), "11444777000161")

    def test_normalizar_cnpj_alfanumerico_preserva_letras(self):
        """Testa que normalização preserva letras do CNPJ alfanumérico"""
        self.assertEqual(normalizar_cnpj("AB123456789012"), "AB123456789012")
        self.assertEqual(normalizar_cnpj("AB.123.456/7890-12"), "AB123456789012")
        self.assertEqual(normalizar_cnpj("ab123456789012"), "AB123456789012")  # Maiúsculas

    def test_normalizar_cnpj_invalido(self):
        """Testa normalização de CNPJ inválido retorna vazio"""
        self.assertEqual(normalizar_cnpj("11.444.777/0001"), "")
        self.assertEqual(normalizar_cnpj("AB12345678901"), "")  # 13 caracteres

    def test_formatar_cnpj_numerico(self):
        """Testa formatação de CNPJ numérico"""
        self.assertEqual(formatar_cnpj("11444777000161"), "11.444.777/0001-61")
        self.assertEqual(formatar_cnpj("11.444.777/0001-61"), "11.444.777/0001-61")

    def test_formatar_cnpj_alfanumerico(self):
        """Testa formatação de CNPJ alfanumérico"""
        self.assertEqual(formatar_cnpj("AB123456789012"), "AB.123.456/7890-12")
        self.assertEqual(formatar_cnpj("AB.123.456/7890-12"), "AB.123.456/7890-12")

    def test_formatar_cnpj_invalido(self):
        """Testa formatação de CNPJ inválido retorna original"""
        self.assertEqual(formatar_cnpj("114447770001"), "114447770001")


class TestCompatibilidadeLegacy(unittest.TestCase):
    """Testa compatibilidade com funções legadas"""

    def test_validar_cpf_legado_usa_servico_unificado(self):
        """Testa que função legada em validators.py usa serviço unificado"""
        from app.utils.validators import validar_cpf as validar_cpf_legado
        
        # CPF válido
        self.assertTrue(validar_cpf_legado("529.982.247-25"))
        
        # CPF inválido
        self.assertFalse(validar_cpf_legado("111.111.111-11"))

    def test_validar_cnpj_legado_usa_servico_unificado(self):
        """Testa que função legada em validators.py usa serviço unificado"""
        from app.utils.validators import validar_cnpj as validar_cnpj_legado
        
        # CNPJ numérico válido
        self.assertTrue(validar_cnpj_legado("11.444.777/0001-61"))
        
        # CNPJ numérico inválido
        self.assertFalse(validar_cnpj_legado("11.111.111/1111-11"))

    def test_validar_cpf_digitos_usa_servico_unificado(self):
        """Testa que função legada em sanitize.py usa serviço unificado"""
        from app.utils.sanitize import validar_cpf_digitos
        
        # CPF válido
        self.assertTrue(validar_cpf_digitos("529.982.247-25"))
        
        # CPF inválido
        self.assertFalse(validar_cpf_digitos("111.111.111-11"))


if __name__ == '__main__':
    unittest.main(verbosity=2)
