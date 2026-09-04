#!/usr/bin/env python3
"""
Validação de Configuração de Variáveis de Ambiente (.env Check)

Este script valida se todas as variáveis do arquivo .env.example
estão configuradas corretamente no ambiente atual e exibe um status formatado.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple


class EnvChecker:
    """Validador de variáveis de ambiente."""

    REQUIRED_VARS = [
        'SECRET_KEY',
    ]

    OPTIONAL_VARS = [
        'DATABASE_URL',
        'MAIL_SERVER',
        'MAIL_PORT',
        'MAIL_USE_TLS',
        'MAIL_USERNAME',
        'MAIL_PASSWORD',
        'TWILIO_ACCOUNT_SID',
        'TWILIO_AUTH_TOKEN',
        'TWILIO_FROM_NUMBER',
    ]

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.env_example_path = self.project_root / '.env.example'
        self.env_path = self.project_root / '.env'

    def load_env_example(self) -> Dict[str, str]:
        """Carrega variáveis do arquivo .env.example."""
        env_vars = {}
        
        if not self.env_example_path.exists():
            print(f"⚠️  Arquivo .env.example não encontrado em {self.env_example_path}")
            return env_vars

        with open(self.env_example_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Ignora comentários e linhas vazias
                if not line or line.startswith('#'):
                    continue
                # Extrai nome e valor
                if '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()

        return env_vars

    def load_current_env(self) -> Dict[str, str]:
        """Carrega variáveis do ambiente atual."""
        env_vars = {}
        
        # Tenta carregar do arquivo .env se existir
        if self.env_path.exists():
            from dotenv import load_dotenv
            load_dotenv(self.env_path)

        # Carrega variáveis do ambiente do sistema
        for key in self.REQUIRED_VARS + self.OPTIONAL_VARS:
            value = os.environ.get(key)
            if value is not None:
                env_vars[key] = value

        return env_vars

    def validate_var(self, key: str, value: str, is_required: bool) -> Tuple[bool, str]:
        """
        Valida uma variável de ambiente.
        
        Returns:
            Tuple[bool, str]: (é_valido, mensagem)
        """
        if not value:
            if is_required:
                return False, "❌ Variável obrigatória não definida"
            else:
                return True, "⚠️  Variável opcional não definida (pode usar padrão)"

        # Validações específicas
        if key == 'SECRET_KEY':
            if len(value) < 16:
                return False, "❌ SECRET_KEY deve ter pelo menos 16 caracteres"
            return True, "✓ Configurado corretamente"

        if key == 'DATABASE_URL':
            if not value.startswith(('sqlite://', 'mysql://', 'postgresql://')):
                return False, "❌ DATABASE_URL deve começar com sqlite://, mysql:// ou postgresql://"
            return True, "✓ Configurado corretamente"

        if key == 'MAIL_PORT':
            try:
                port = int(value)
                if not (1 <= port <= 65535):
                    return False, "❌ MAIL_PORT deve ser entre 1 e 65535"
                return True, "✓ Configurado corretamente"
            except ValueError:
                return False, "❌ MAIL_PORT deve ser um número inteiro"

        if key == 'MAIL_USE_TLS':
            if value.lower() not in ('true', 'false', ''):
                return False, "❌ MAIL_USE_TLS deve ser 'true' ou 'false'"
            return True, "✓ Configurado corretamente"

        if key.startswith('TWILIO_'):
            if key == 'TWILIO_ACCOUNT_SID' and not value.startswith('AC'):
                return False, "❌ TWILIO_ACCOUNT_SID deve começar com 'AC'"
            if key == 'TWILIO_FROM_NUMBER' and not value.startswith('+'):
                return False, "❌ TWILIO_FROM_NUMBER deve começar com '+'"
            return True, "✓ Configurado corretamente"

        return True, "✓ Configurado corretamente"

    def check(self) -> bool:
        """
        Executa verificação completa das variáveis de ambiente.
        
        Returns:
            bool: True se todas as obrigatórias estão OK, False caso contrário
        """
        print("=" * 70)
        print("🔍 VALIDAÇÃO DE VARIÁVEIS DE AMBIENTE - RedeVita")
        print("=" * 70)
        print()

        example_vars = self.load_env_example()
        current_vars = self.load_current_env()

        all_required_ok = True
        total_vars = 0
        ok_vars = 0

        # Verifica variáveis obrigatórias
        print("📋 VARIÁVEIS OBRIGATÓRIAS:")
        print("-" * 70)
        
        for var in self.REQUIRED_VARS:
            total_vars += 1
            value = current_vars.get(var, '')
            is_valid, message = self.validate_var(var, value, is_required=True)
            
            if is_valid:
                ok_vars += 1
                print(f"  {var:30s} {message}")
            else:
                all_required_ok = False
                print(f"  {var:30s} {message}")

        print()

        # Verifica variáveis opcionais
        print("📋 VARIÁVEIS OPCIONAIS:")
        print("-" * 70)
        
        for var in self.OPTIONAL_VARS:
            total_vars += 1
            value = current_vars.get(var, '')
            is_valid, message = self.validate_var(var, value, is_required=False)
            
            if is_valid and '✓' in message:
                ok_vars += 1
            print(f"  {var:30s} {message}")

        print()
        print("=" * 70)
        
        # Resumo
        percentage = (ok_vars / total_vars * 100) if total_vars > 0 else 0
        
        if all_required_ok:
            print(f"✅ STATUS: TODAS AS VARIÁVEIS OBRIGATÓRIAS ESTÃO CONFIGURADAS")
            print(f"   Progresso: {ok_vars}/{total_vars} variáveis ({percentage:.1f}%)")
            print()
            return True
        else:
            print(f"❌ STATUS: VARIÁVEIS OBRIGATÓRIAS FALTANDO")
            print(f"   Progresso: {ok_vars}/{total_vars} variáveis ({percentage:.1f}%)")
            print()
            print("💡 Ação recomendada:")
            print("   1. Copie .env.example para .env")
            print("   2. Configure as variáveis obrigatórias no arquivo .env")
            print()
            return False

    def check_dependencies(self) -> bool:
        """Verifica se as dependências necessárias estão instaladas."""
        print("=" * 70)
        print("📦 VERIFICANDO DEPENDÊNCIAS:")
        print("-" * 70)
        
        missing = []
        
        try:
            import dotenv
            print("  ✓ python-dotenv instalado")
        except ImportError:
            print("  ❌ python-dotenv NÃO instalado")
            missing.append("python-dotenv")

        if missing:
            print()
            print(f"⚠️  Dependências faltando: {', '.join(missing)}")
            print("💡 Instale com: pip install " + " ".join(missing))
            print()
            return False
        
        print()
        return True


def main():
    """Função principal."""
    checker = EnvChecker()
    
    # Verifica dependências
    deps_ok = checker.check_dependencies()
    
    # Verifica variáveis de ambiente
    env_ok = checker.check()
    
    # Exit code
    if deps_ok and env_ok:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
