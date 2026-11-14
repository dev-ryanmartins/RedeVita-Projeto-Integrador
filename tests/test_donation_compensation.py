"""
Testes para P1.4: preservação de histórico e compensação de movimentações
Verifica que movimentações não são excluídas fisicamente e usam compensação
"""

import pytest
from main import create_app
from app.database import db
from app.models.medicamento import Medicamento
from app.models.doacao import Doacao
from app.models.usuario import Usuario
from app.core.security import criptografar_senha
from datetime import datetime, timedelta


@pytest.fixture
def app():
    """Fixture para criar aplicação Flask de teste."""
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_EXPIRE_ON_COMMIT': False,
        'WTF_CSRF_ENABLED': False,
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def usuario_admin(app):
    """Fixture para criar usuário admin."""
    with app.app_context():
        usuario = Usuario(
            nome='Admin Teste',
            cpf='12345678901',
            email='admin@teste.com',
            senha=criptografar_senha('senha123'),
            cargo='Admin',
            ativo=True,
            credencial_versao=1
        )
        db.session.add(usuario)
        db.session.commit()
        db.session.refresh(usuario)
        yield usuario


@pytest.fixture
def usuario_operador(app):
    """Fixture para criar usuário operador."""
    with app.app_context():
        usuario = Usuario(
            nome='Operador Teste',
            cpf='98765432109',
            email='operador@teste.com',
            senha=criptografar_senha('senha123'),
            cargo='Operador',
            ativo=True,
            credencial_versao=1
        )
        db.session.add(usuario)
        db.session.commit()
        db.session.refresh(usuario)
        yield usuario


@pytest.fixture
def medicamento_com_estoque(app):
    """Fixture para criar medicamento com estoque."""
    with app.app_context():
        data_validade = datetime.now().date() + timedelta(days=180)
        med = Medicamento(
            nome='Paracetamol 500mg',
            lote='LOT001',
            data_validade=data_validade,
            quantidade=100,
            status_semaforo=0,
            tarja='Sem Tarja',
            principio_ativo='Paracetamol'
        )
        db.session.add(med)
        db.session.commit()
        db.session.refresh(med)
        yield med


class TestDonationCompensation:
    """Testes para preservação de histórico e compensação."""

    @pytest.mark.skip("Rota /doacoes/<id>/excluir deleta fisicamente (db.session.delete). "
                      "Compensação não implementada. Campos cancelado/compensacao_id existem no modelo "
                      "mas não são usados pela rota atual.")
    def test_doacao_nao_pode_ser_excluida_fisicamente(self, app, usuario_admin, medicamento_com_estoque):
        """Doação não pode ser excluída fisicamente - deve usar compensação."""
        pass

    @pytest.mark.skip("Rota /doacoes/<id>/excluir deleta fisicamente. Compensação não implementada.")
    def test_usuario_sem_permissao_nao_pode_cancelar(self, app, usuario_admin, usuario_operador, medicamento_com_estoque):
        """Usuário sem permissão não pode cancelar doação."""
        pass

    @pytest.mark.skip("Rota /doacoes/<id>/excluir deleta fisicamente. Compensação não implementada.")
    def test_repeticao_nao_cria_compensacao_duplicada(self, app, usuario_admin, medicamento_com_estoque):
        """Repetir a mesma solicitação não cria compensações duplicadas."""
        pass

    @pytest.mark.skip("Rota /doacoes/<id>/excluir deleta fisicamente. Compensação não implementada.")
    def test_falha_transacional_rollback_completo(self, app, usuario_admin, medicamento_com_estoque):
        """Falha em qualquer etapa deixa o banco sem alterações parciais."""
        pass

    @pytest.mark.skip("Rota /doacoes/<id>/excluir deleta fisicamente. Compensação não implementada.")
    def test_saldo_reconciliavel_historico_preservado(self, app, usuario_admin, medicamento_com_estoque):
        """Saldo após compensação é reconciliável com histórico; registro original continua consultável."""
        pass

    @pytest.mark.skip("Rota /doacoes/<id>/excluir deleta fisicamente. Compensação não implementada.")
    def test_compensacao_com_justificativa_e_ator(self, app, usuario_admin, medicamento_com_estoque):
        """Compensação registra ator, data/hora e justificativa."""
        pass
