"""
Test Decorators - Suíte de Testes de Decoradores de Acesso
Testa os decoradores de controle de acesso e permissões
"""

import unittest
import sys
import os

# Adiciona o diretório backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.core.decorators import (
    _cargo_normalizado,
    cargo_permitido,
)


class TestDecorators(unittest.TestCase):
    """Testa os decoradores de controle de acesso"""
    
    def test_cargo_normalizado_admin(self):
        """Testa normalização do cargo Admin"""
        variants = ['admin', 'Admin', 'ADMIN', ' aDmIn ']
        for variant in variants:
            result = _cargo_normalizado(variant)
            self.assertEqual(result, 'Admin', f"Cargo '{variant}' deve normalizar para 'Admin'")
    
    def test_cargo_normalizado_operador(self):
        """Testa normalização do cargo Operador"""
        variants = ['operador', 'Operador', 'receptor', 'Receptor']
        for variant in variants:
            result = _cargo_normalizado(variant)
            self.assertEqual(result, 'Operador', f"Cargo '{variant}' deve normalizar para 'Operador'")
    
    def test_cargo_normalizado_voluntario(self):
        """Testa normalização do cargo Voluntário"""
        variants = ['voluntario', 'Voluntário', 'voluntário', 'VOLUNTARIO']
        for variant in variants:
            result = _cargo_normalizado(variant)
            self.assertEqual(result, 'Voluntário', f"Cargo '{variant}' deve normalizar para 'Voluntário'")
    
    def test_cargo_normalizado_medico(self):
        """Testa normalização do cargo Médico"""
        variants = ['medico', 'Médico', 'médico', 'MEDICO']
        for variant in variants:
            result = _cargo_normalizado(variant)
            self.assertEqual(result, 'Médico', f"Cargo '{variant}' deve normalizar para 'Médico'")
    
    def test_cargo_normalizado_farmaceutico(self):
        """Testa normalização do cargo Farmacêutico"""
        variants = ['farmaceutico', 'Farmacêutico', 'farmacêutico', 'FARMACEUTICO']
        for variant in variants:
            result = _cargo_normalizado(variant)
            self.assertEqual(result, 'Farmacêutico', f"Cargo '{variant}' deve normalizar para 'Farmacêutico'")
    
    def test_cargo_normalizado_doador(self):
        """Testa normalização do cargo Doador"""
        variants = ['doador', 'Doador', 'DOADOR']
        for variant in variants:
            result = _cargo_normalizado(variant)
            self.assertEqual(result, 'Doador', f"Cargo '{variant}' deve normalizar para 'Doador'")
    
    def test_cargo_normalizado_vazio(self):
        """Testa normalização de cargo vazio"""
        result = _cargo_normalizado('')
        self.assertEqual(result, '', "Cargo vazio deve retornar string vazia")
        
        result = _cargo_normalizado(None)
        self.assertEqual(result, '', "Cargo None deve retornar string vazia")
    
    def test_cargo_normalizado_desconhecido(self):
        """Testa normalização de cargo desconhecido"""
        result = _cargo_normalizado('CargoDesconhecido')
        self.assertEqual(result, 'CargoDesconhecido', "Cargo desconhecido deve retornar o valor original")
    
    def test_cargo_permitido_admin(self):
        """Testa permissão para cargo Admin"""
        self.assertTrue(cargo_permitido('Admin', ['Admin']))
        self.assertTrue(cargo_permitido('admin', ['Admin']))
        self.assertTrue(cargo_permitido('Admin', ['Admin', 'Operador']))
        self.assertFalse(cargo_permitido('Admin', ['Operador']))
    
    def test_cargo_permitido_multiplas_opcoes(self):
        """Testa permissão com múltiplas opções de cargo"""
        self.assertTrue(cargo_permitido('Admin', ['Admin', 'Operador', 'Médico']))
        self.assertTrue(cargo_permitido('Operador', ['Admin', 'Operador', 'Médico']))
        self.assertTrue(cargo_permitido('Médico', ['Admin', 'Operador', 'Médico']))
        self.assertFalse(cargo_permitido('Voluntário', ['Admin', 'Operador', 'Médico']))
    
    def test_cargo_permitido_variacoes_case(self):
        """Testa permissão com variações de maiúsculas/minúsculas"""
        self.assertTrue(cargo_permitido('admin', ['Admin']))
        self.assertTrue(cargo_permitido('ADMIN', ['Admin']))
        self.assertTrue(cargo_permitido('médico', ['Médico']))
        self.assertTrue(cargo_permitido('MÉDICO', ['Médico']))
    
    def test_cargo_permitido_receptor_como_operador(self):
        """Testa que 'receptor' é tratado como 'Operador'"""
        self.assertTrue(cargo_permitido('receptor', ['Operador']))
        self.assertTrue(cargo_permitido('Receptor', ['Operador']))
        self.assertTrue(cargo_permitido('operador', ['Operador']))
    
    def test_cargo_permitido_lista_vazia(self):
        """Testa permissão com lista vazia de cargos permitidos"""
        self.assertFalse(cargo_permitido('Admin', []))
        self.assertFalse(cargo_permitido('Operador', []))
    
    def test_cargo_permitido_cargo_usuario_vazio(self):
        """Testa permissão com cargo do usuário vazio"""
        self.assertFalse(cargo_permitido('', ['Admin']))
        self.assertFalse(cargo_permitido(None, ['Admin']))
    
    def test_cargo_permitido_equipe_clinica(self):
        """Testa permissão para equipe clínica (Admin, Operador, Médico, Farmacêutico)"""
        equipe_clinica = ['Admin', 'Operador', 'Médico', 'Farmacêutico']
        
        self.assertTrue(cargo_permitido('Admin', equipe_clinica))
        self.assertTrue(cargo_permitido('Operador', equipe_clinica))
        self.assertTrue(cargo_permitido('Médico', equipe_clinica))
        self.assertTrue(cargo_permitido('Farmacêutico', equipe_clinica))
        
        self.assertFalse(cargo_permitido('Voluntário', equipe_clinica))
        self.assertFalse(cargo_permitido('Doador', equipe_clinica))


if __name__ == '__main__':
    unittest.main(verbosity=2)
