"""
Testes para P1.3: evitar seleção ambígua de lote na saída de doação
Verifica que saída exige ID explícito e não usa busca por nome parcial
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
def usuario_operador(app):
    """Fixture para criar usuário operador."""
    with app.app_context():
        usuario = Usuario(
            nome='Operador Teste',
            cpf='12345678901',
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
def medicamentos_similares(app):
    """Fixture para criar medicamentos com nomes parecidos."""
    with app.app_context():
        data_validade = datetime.now().date() + timedelta(days=180)
        
        med1 = Medicamento(
            nome='Paracetamol 500mg',
            lote='LOT001',
            data_validade=data_validade,
            quantidade=100,
            status_semaforo=0,
            tarja='Sem Tarja',
            principio_ativo='Paracetamol'
        )
        
        med2 = Medicamento(
            nome='Paracetamol 750mg',
            lote='LOT002',
            data_validade=data_validade,
            quantidade=50,
            status_semaforo=0,
            tarja='Sem Tarja',
            principio_ativo='Paracetamol'
        )
        
        med3 = Medicamento(
            nome='Paracetamol Infantil',
            lote='LOT003',
            data_validade=data_validade,
            quantidade=30,
            status_semaforo=0,
            tarja='Sem Tarja',
            principio_ativo='Paracetamol'
        )
        
        db.session.add_all([med1, med2, med3])
        db.session.commit()
        db.session.refresh(med1)
        db.session.refresh(med2)
        db.session.refresh(med3)
        yield [med1, med2, med3]


class TestDonationAmbiguousSelection:
    """Testes para evitar seleção ambígua na saída de doação."""
    
    def test_nome_parcial_nao_executa_saida(self, app, usuario_operador, medicamentos_similares):
        """Nome parcial ou nome livre sozinho não deve executar saída."""
        med1, med2, med3 = medicamentos_similares
        
        with app.test_client() as client:
            # Login
            client.post('/login', data={
                'identificador': '12345678901',
                'senha': 'senha123'
            }, follow_redirects=True)
            
            # Tentar saída com apenas nome parcial (sem medicamento_id - comportamento legado deve ser rejeitado)
            response = client.post('/doacoes', data={
                'medicamento_nome': 'Paracetamol',
                'quantidade': '10',
                'receita_medica': 'REC123',
                'aprovacao_farmaceutico': 'aprovado',
                'csrf_token': 'dummy'
            }, follow_redirects=False)
            
            # Deve ser rejeitado (flash message de erro)
            with app.app_context():
                # Verificar que nenhum estoque foi alterado
                med1_check = db.session.get(Medicamento, med1.id)
                med2_check = db.session.get(Medicamento, med2.id)
                med3_check = db.session.get(Medicamento, med3.id)
                
                assert med1_check.quantidade == 100, "Estoque não deve ter sido alterado"
                assert med2_check.quantidade == 50, "Estoque não deve ter sido alterado"
                assert med3_check.quantidade == 30, "Estoque não deve ter sido alterado"
                
                # Verificar que não houve registro de doação
                doacoes = Doacao.query.all()
                assert len(doacoes) == 0, "Nenhuma doação deve ter sido registrada"
    
    def test_saida_requer_id_explicito(self, app, usuario_operador, medicamentos_similares):
        """Saída deve exigir ID explícito do medicamento."""
        med1, med2, med3 = medicamentos_similares
        
        with app.test_client() as client:
            # Login
            client.post('/login', data={
                'identificador': '12345678901',
                'senha': 'senha123'
            }, follow_redirects=True)
            
            # Tentar saída com ID explícito
            response = client.post('/doacoes', data={
                'medicamento_id': str(med1.id),
                'quantidade': '10',
                'receita_medica': 'REC123',
                'aprovacao_farmaceutico': 'aprovado',
                'csrf_token': 'dummy'
            }, follow_redirects=False)
            
            # Após correção, deve aceitar e baixar do medicamento correto
            with app.app_context():
                med1_check = db.session.get(Medicamento, med1.id)
                assert med1_check.quantidade == 90, f"Estoque deve ter sido reduzido em 10, mas é {med1_check.quantidade}"
    
    def test_multiplos_nomes_parecidos_nao_ambiguos(self, app, usuario_operador, medicamentos_similares):
        """Múltiplos medicamentos com nomes parecidos não devem causar ambiguidade."""
        med1, med2, med3 = medicamentos_similares
        
        with app.test_client() as client:
            # Login
            client.post('/login', data={
                'identificador': '12345678901',
                'senha': 'senha123'
            }, follow_redirects=True)
            
            # Saída para med2 especificamente
            response = client.post('/doacoes', data={
                'medicamento_id': str(med2.id),
                'quantidade': '5',
                'receita_medica': 'REC456',
                'aprovacao_farmaceutico': 'aprovado',
                'csrf_token': 'dummy'
            }, follow_redirects=False)
            
            with app.app_context():
                med1_check = db.session.get(Medicamento, med1.id)
                med2_check = db.session.get(Medicamento, med2.id)
                med3_check = db.session.get(Medicamento, med3.id)
                
                # Apenas med2 deve ter sido alterado
                assert med1_check.quantidade == 100, "med1 não deve ter sido alterado"
                assert med2_check.quantidade == 45, f"med2 deve ter sido reduzido em 5, mas é {med2_check.quantidade}"
                assert med3_check.quantidade == 30, "med3 não deve ter sido alterado"
    
    def test_id_inexistente_rejeitado(self, app, usuario_operador, medicamentos_similares):
        """ID inexistente deve ser rejeitado."""
        with app.test_client() as client:
            # Login
            client.post('/login', data={
                'identificador': '12345678901',
                'senha': 'senha123'
            }, follow_redirects=True)
            
            # Tentar saída com ID inexistente
            response = client.post('/doacoes', data={
                'medicamento_id': '99999',
                'quantidade': '10',
                'receita_medica': 'REC789',
                'aprovacao_farmaceutico': 'aprovado',
                'csrf_token': 'dummy'
            }, follow_redirects=False)
            
            # Deve ser rejeitado
            with app.app_context():
                # Verificar que não houve alterações
                medicamentos = Medicamento.query.all()
                for med in medicamentos:
                    assert med.quantidade > 0, "Nenhum estoque deve ter sido alterado"
                
                # Verificar que não houve registro de doação
                doacoes = Doacao.query.all()
                assert len(doacoes) == 0, "Nenhuma doação deve ter sido registrada"
    
    def test_payload_legado_com_texto_parcial_sem_efeito(self, app, usuario_operador, medicamentos_similares):
        """Payload legado com texto parcial não deve ter efeito."""
        med1, med2, med3 = medicamentos_similares
        
        with app.test_client() as client:
            # Login
            client.post('/login', data={
                'identificador': '12345678901',
                'senha': 'senha123'
            }, follow_redirects=True)
            
            # Payload legado (sem medicamento_id, apenas nome)
            response = client.post('/doacoes', data={
                'medicamento_nome': 'Paracetamol',
                'quantidade': '10',
                'receita_medica': 'REC999',
                'aprovacao_farmaceutico': 'aprovado',
                'csrf_token': 'dummy'
            }, follow_redirects=False)
            
            with app.app_context():
                med1_check = db.session.get(Medicamento, med1.id)
                med2_check = db.session.get(Medicamento, med2.id)
                med3_check = db.session.get(Medicamento, med3.id)
                
                # Nenhum deve ter sido alterado
                assert med1_check.quantidade == 100
                assert med2_check.quantidade == 50
                assert med3_check.quantidade == 30
                
                # Verificar que não houve registro de doação
                doacoes = Doacao.query.all()
                assert len(doacoes) == 0, "Nenhuma doação deve ter sido registrada"
    
    def test_lote_vencido_rejeitado(self, app, usuario_operador):
        """Lote vencido deve ser rejeitado."""
        with app.app_context():
            data_vencida = datetime.now().date() - timedelta(days=30)
            med_vencido = Medicamento(
                nome='Medicamento Vencido',
                lote='LOT-VENCIDO',
                data_validade=data_vencida,
                quantidade=50,
                status_semaforo=2,  # Vermelho (vencido)
                tarja='Sem Tarja',
                principio_ativo='Teste'
            )
            db.session.add(med_vencido)
            db.session.commit()
            db.session.refresh(med_vencido)
        
        with app.test_client() as client:
            # Login
            client.post('/login', data={
                'identificador': '12345678901',
                'senha': 'senha123'
            }, follow_redirects=True)
            
            # Tentar saída de lote vencido
            response = client.post('/doacoes', data={
                'medicamento_id': str(med_vencido.id),
                'quantidade': '10',
                'csrf_token': 'dummy'
            }, follow_redirects=False)
            
            with app.app_context():
                med_check = db.session.get(Medicamento, med_vencido.id)
                assert med_check.quantidade == 50, "Estoque não deve ter sido alterado"
                
                # Verificar que não houve registro de doação
                doacoes = Doacao.query.all()
                assert len(doacoes) == 0, "Nenhuma doação deve ter sido registrada"
    
    def test_saldo_insuficiente_rejeitado(self, app, usuario_operador):
        """Saldo insuficiente deve ser rejeitado."""
        with app.app_context():
            data_validade = datetime.now().date() + timedelta(days=180)
            med_pouco_estoque = Medicamento(
                nome='Medicamento Pouco Estoque',
                lote='LOT-POUCO',
                data_validade=data_validade,
                quantidade=5,
                status_semaforo=0,
                tarja='Sem Tarja',
                principio_ativo='Teste'
            )
            db.session.add(med_pouco_estoque)
            db.session.commit()
            db.session.refresh(med_pouco_estoque)
        
        with app.test_client() as client:
            # Login
            client.post('/login', data={
                'identificador': '12345678901',
                'senha': 'senha123'
            }, follow_redirects=True)
            
            # Tentar saída maior que estoque
            response = client.post('/doacoes', data={
                'medicamento_id': str(med_pouco_estoque.id),
                'quantidade': '10',  # Mais que o estoque de 5
                'csrf_token': 'dummy'
            }, follow_redirects=False)
            
            with app.app_context():
                med_check = db.session.get(Medicamento, med_pouco_estoque.id)
                assert med_check.quantidade == 5, "Estoque não deve ter sido alterado"
                
                # Verificar que não houve registro de doação
                doacoes = Doacao.query.all()
                assert len(doacoes) == 0, "Nenhuma doação deve ter sido registrada"
    
    def test_tentativa_adulteracao_id_rejeitada(self, app, usuario_operador, medicamentos_similares):
        """Tentativa de adulteração de ID deve ser rejeitada."""
        med1, med2, med3 = medicamentos_similares
        
        with app.test_client() as client:
            # Login
            client.post('/login', data={
                'identificador': '12345678901',
                'senha': 'senha123'
            }, follow_redirects=True)
            
            # Tentar adulterar ID (ex: mudar de med1.id para med2.id no payload)
            # Mas como o teste não pode interceptar, testamos ID inválido
            response = client.post('/doacoes', data={
                'medicamento_id': 'abc123',  # ID não numérico
                'quantidade': '10',
                'csrf_token': 'dummy'
            }, follow_redirects=False)
            
            with app.app_context():
                # Verificar que não houve alterações
                med1_check = db.session.get(Medicamento, med1.id)
                med2_check = db.session.get(Medicamento, med2.id)
                med3_check = db.session.get(Medicamento, med3.id)
                
                assert med1_check.quantidade == 100
                assert med2_check.quantidade == 50
                assert med3_check.quantidade == 30
                
                # Verificar que não houve registro de doação
                doacoes = Doacao.query.all()
                assert len(doacoes) == 0
