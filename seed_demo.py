"""
Prepara uma base fake para apresentação do RedeVita.

Credenciais criadas:
  Admin        | CPF 00000000000 | senha admin123
  Voluntário   | CPF 22244466671 | senha demo1234
  Farmacêutico | CPF 33355577782 | senha demo1234
  Médico       | CPF 44466688893 | senha demo1234
  Receptor     | CPF 55577799902 | senha demo1234

Uso:
  python seed_demo.py
"""

from app.utils.semaforo import calcular_status_semaforo
from app.models.usuario import Usuario
from app.models.receita import Receita
from app.models.paciente import Paciente
from app.models.medico import Medico
from app.models.medicamento import Medicamento
from app.models.log_atividade import LogAtividade
from app.models.farmacia import Farmacia
from app.models.doacao import Doacao
from app.database import db
from app.core.security import criptografar_senha
from main import create_app
import os
import sys
from datetime import UTC, date, datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))


SENHA_DEMO = 'demo1234'

USUARIOS = [
    {
        'nome': 'Administrador RedeVita',
        'cpf': '00000000000',
        'email': 'admin@redevita.local',
        'senha': 'admin123',
        'cargo': 'Admin',
    },
    {
        'nome': 'Ana Clara Voluntaria',
        'cpf': '22244466671',
        'email': 'voluntario.demo@redevita.local',
        'senha': SENHA_DEMO,
        'cargo': 'Voluntário',
    },
    {
        'nome': 'Marina Souza Farmaceutica',
        'cpf': '33355577782',
        'email': 'farmaceutico.demo@redevita.local',
        'senha': SENHA_DEMO,
        'cargo': 'Farmacêutico',
    },
    {
        'nome': 'Dr. Rafael Almeida',
        'cpf': '44466688893',
        'email': 'medico.demo@redevita.local',
        'senha': SENHA_DEMO,
        'cargo': 'Médico',
    },
    {
        'nome': 'Lucas Pereira Receptor',
        'cpf': '55577799902',
        'email': 'receptor.demo@redevita.local',
        'senha': SENHA_DEMO,
        'cargo': 'Operador',
    },
]


def agora():
    return datetime.now(UTC).replace(tzinfo=None)


MEDICAMENTOS = [
    {
        'nome': 'Dipirona 500mg',
        'lote': 'DEMO-DIP-2401',
        'validade': date.today() + timedelta(days=420),
        'quantidade': 180,
        'tarja': 'Sem Tarja',
        'principio_ativo': 'Dipirona Sódica',
        'uso_continuo': False,
    },
    {
        'nome': 'Paracetamol 750mg',
        'lote': 'DEMO-PAR-2402',
        'validade': date.today() + timedelta(days=210),
        'quantidade': 95,
        'tarja': 'Sem Tarja',
        'principio_ativo': 'Paracetamol',
        'uso_continuo': False,
    },
    {
        'nome': 'Amoxicilina 500mg',
        'lote': 'DEMO-AMX-2403',
        'validade': date.today() + timedelta(days=80),
        'quantidade': 42,
        'tarja': 'Tarja Vermelha',
        'principio_ativo': 'Amoxicilina',
        'uso_continuo': False,
    },
    {
        'nome': 'Losartana 50mg',
        'lote': 'DEMO-LOS-2404',
        'validade': date.today() + timedelta(days=365),
        'quantidade': 130,
        'tarja': 'Tarja Vermelha',
        'principio_ativo': 'Losartana Potássica',
        'uso_continuo': True,
    },
    {
        'nome': 'Clonazepam 0,5mg',
        'lote': 'DEMO-CLO-2405',
        'validade': date.today() + timedelta(days=300),
        'quantidade': 28,
        'tarja': 'Portaria 344',
        'principio_ativo': 'Clonazepam',
        'uso_continuo': True,
    },
    {
        'nome': 'Ibuprofeno 600mg',
        'lote': 'DEMO-IBU-2406',
        'validade': date.today() + timedelta(days=25),
        'quantidade': 18,
        'tarja': 'Tarja Vermelha',
        'principio_ativo': 'Ibuprofeno',
        'uso_continuo': False,
    },
    {
        'nome': 'Omeprazol 20mg',
        'lote': 'DEMO-OME-2407',
        'validade': date.today() - timedelta(days=12),
        'quantidade': 0,
        'tarja': 'Tarja Vermelha',
        'principio_ativo': 'Omeprazol',
        'uso_continuo': True,
    },
    # Medicamentos adicionais para demonstração mais rica
    {
        'nome': 'Metformina 850mg',
        'lote': 'DEMO-MET-2408',
        'validade': date.today() + timedelta(days=180),
        'quantidade': 65,
        'tarja': 'Tarja Vermelha',
        'principio_ativo': 'Metformina',
        'uso_continuo': True,
    },
    {
        'nome': 'Diazepam 10mg',
        'lote': 'DEMO-DIA-2409',
        'validade': date.today() + timedelta(days=90),
        'quantidade': 35,
        'tarja': 'Portaria 344',
        'principio_ativo': 'Diazepam',
        'uso_continuo': True,
    },
    {
        'nome': 'Captopril 25mg',
        'lote': 'DEMO-CAP-2410',
        'validade': date.today() + timedelta(days=270),
        'quantidade': 88,
        'tarja': 'Tarja Vermelha',
        'principio_ativo': 'Captopril',
        'uso_continuo': True,
    },
    {
        'nome': 'Risperidona 2mg',
        'lote': 'DEMO-RIS-2411',
        'validade': date.today() + timedelta(days=150),
        'quantidade': 22,
        'tarja': 'Tarja Amarela',
        'principio_ativo': 'Risperidona',
        'uso_continuo': True,
    },
    {
        'nome': 'Insulina NPH 100 UI/mL',
        'lote': 'DEMO-INS-2412',
        'validade': date.today() + timedelta(days=60),
        'quantidade': 15,
        'tarja': 'Tarja Vermelha',
        'principio_ativo': 'Insulina Humana NPH',
        'uso_continuo': True,
    },
    {
        'nome': 'Ácido Fólico 5mg',
        'lote': 'DEMO-ACI-2413',
        'validade': date.today() + timedelta(days=450),
        'quantidade': 200,
        'tarja': 'Sem Tarja',
        'principio_ativo': 'Ácido Fólico',
        'uso_continuo': False,
    },
    {
        'nome': 'Vitamina D3 2000UI',
        'lote': 'DEMO-VIT-2414',
        'validade': date.today() + timedelta(days=300),
        'quantidade': 150,
        'tarja': 'Sem Tarja',
        'principio_ativo': 'Colecalciferol',
        'uso_continuo': False,
    },
    {
        'nome': 'Aspirina 100mg',
        'lote': 'DEMO-ASP-2415',
        'validade': date.today() + timedelta(days=240),
        'quantidade': 120,
        'tarja': 'Tarja Amarela',
        'principio_ativo': 'Ácido Acetilsalicílico',
        'uso_continuo': True,
    },
]

PACIENTES = [
    ('Carlos Eduardo Lima',
     '10120230344',
     date(
         1978,
         5,
         14),
        'Rua das Acácias, 120 - Sorocaba/SP'),
    ('Maria Helena Costa',
     '20230340455',
     date(
         1956,
         9,
         3),
     'Av. Brasil, 875 - Sorocaba/SP'),
    ('João Pedro Martins',
     '30340450566',
     date(
         2012,
         2,
         18),
     'Rua Itavuvu, 441 - Sorocaba/SP'),
    ('Fernanda Oliveira Rocha',
     '40450560677',
     date(
         1989,
         11,
         27),
     'Rua XV de Novembro, 88 - Sorocaba/SP'),
    # Pacientes adicionais para demonstração mais rica
    ('Roberto Silva Santos',
     '50560670788',
     date(
         1965,
         8,
         22),
     'Rua das Flores, 234 - Sorocaba/SP'),
    ('Ana Paula Ferreira',
     '60670780899',
     date(
         1992,
         4,
         15),
     'Av. Independência, 567 - Sorocaba/SP'),
    ('José Carlos Oliveira',
     '70780890900',
     date(
         1950,
         12,
         3),
     'Rua São Paulo, 890 - Sorocaba/SP'),
    ('Mariana Rodrigues Lima',
     '80890901011',
     date(
         1985,
         7,
         30),
     'Av. Murilo Braga, 123 - Sorocaba/SP'),
    ('Pedro Henrique Costa',
     '90901011122',
     date(
         2000,
         1,
         18),
     'Rua do Comércio, 456 - Sorocaba/SP'),
    ('Juliana Maria Alves',
     '01011121233',
     date(
         1972,
         10,
         5),
     'Av. Portugal, 789 - Sorocaba/SP'),
]

MEDICOS = [
    ('Dra. Beatriz Campos', 'CRM-SP 118245', 'Clínica Geral', '(15) 99111-2200'),
    ('Dr. Rafael Almeida', 'CRM-SP 135790', 'Cardiologia', '(15) 99222-3300'),
    ('Dra. Camila Nogueira', 'CRM-SP 142680', 'Pediatria', '(15) 99333-4400'),
    # Médicos adicionais para demonstração mais rica
    ('Dr. Fernando Costa', 'CRM-SP 156789', 'Psiquiatria', '(15) 99444-5500'),
    ('Dra. Patricia Mendes', 'CRM-SP 167890', 'Endocrinologia', '(15) 99555-6600'),
    ('Dr. Lucas Rodrigues', 'CRM-SP 178901', 'Ortopedia', '(15) 99666-7700'),
]

FARMACIAS = [
    (
        'Farmácia Solidária Centro',
        'RedeVita Farmácia Solidária LTDA',
        '12.345.678/0001-90',
        'Rua Padre Luiz, 45 - Centro, Sorocaba/SP',
        'Marina Souza',
    ),
    (
        'Ponto de Apoio Zona Norte',
        'RedeVita Apoio Comunitário LTDA',
        '98.765.432/0001-10',
        'Av. Itavuvu, 2300 - Sorocaba/SP',
        'Lucas Pereira',
    ),
    (
        'Unidade Parceira Campolim',
        'Instituto RedeVita Saúde',
        '45.123.789/0001-55',
        'Av. Antônio Carlos Comitre, 900 - Sorocaba/SP',
        'Ana Clara',
    ),
    # Farmácias adicionais para demonstração mais rica
    (
        'Farmácia Esperança Éden',
        'Farmácia Esperança Éden LTDA',
        '23.456.789/0001-23',
        'Rua do Éden, 150 - Sorocaba/SP',
        'Carlos Mendes',
    ),
    (
        'Drogaria Vida Nova',
        'Drogaria Vida Nova ME',
        '34.567.890/0001-34',
        'Av. Washington Luiz, 500 - Sorocaba/SP',
        'Fernanda Lima',
    ),
]


def upsert_usuario(dados):
    usuario = Usuario.query.filter_by(cpf=dados['cpf']).first()
    if not usuario:
        usuario = Usuario(cpf=dados['cpf'])
        db.session.add(usuario)

    usuario.nome = dados['nome']
    usuario.email = dados['email']
    usuario.senha = criptografar_senha(dados['senha'])
    usuario.cargo = dados['cargo']
    usuario.ativo = True
    return usuario


def upsert_medicamento(dados):
    med = Medicamento.query.filter_by(lote=dados['lote']).first()
    if not med:
        med = Medicamento(lote=dados['lote'])
        db.session.add(med)

    med.nome = dados['nome']
    med.data_validade = dados['validade']
    med.quantidade = dados['quantidade']
    med.status_semaforo = calcular_status_semaforo(dados['validade'])
    med.tarja = dados['tarja']
    med.principio_ativo = dados['principio_ativo']
    med.uso_continuo = dados['uso_continuo']
    return med


def upsert_paciente(nome, cpf, nascimento, endereco):
    paciente = Paciente.query.filter_by(cpf=cpf).first()
    if not paciente:
        paciente = Paciente(cpf=cpf)
        db.session.add(paciente)

    paciente.nome = nome
    paciente.data_nascimento = nascimento
    paciente.endereco = endereco
    return paciente


def upsert_medico(nome, crm, especialidade, contato):
    medico = Medico.query.filter_by(crm=crm).first()
    if not medico:
        medico = Medico(crm=crm)
        db.session.add(medico)

    medico.nome = nome
    medico.especialidade = especialidade
    medico.contato = contato
    return medico


def upsert_farmacia(nome, razao, cnpj, endereco, responsavel):
    farmacia = Farmacia.query.filter_by(cnpj=cnpj).first()
    if not farmacia:
        farmacia = Farmacia(cnpj=cnpj)
        db.session.add(farmacia)

    farmacia.nome_fantasia = nome
    farmacia.razao_social = razao
    farmacia.endereco = endereco
    farmacia.responsavel = responsavel
    return farmacia


def criar_doacao(usuario, medicamento, quantidade, dias_atras):
    existente = Doacao.query.filter_by(
        usuario_id=usuario.id,
        medicamento_id=medicamento.id,
        quantidade=quantidade,
    ).first()
    if existente:
        existente.data_doacao = agora() - timedelta(days=dias_atras)
        return existente

    doacao = Doacao(
        usuario_id=usuario.id,
        medicamento_id=medicamento.id,
        quantidade=quantidade,
        data_doacao=agora() - timedelta(days=dias_atras),
    )
    db.session.add(doacao)
    return doacao


def criar_receita(
        paciente,
        medico,
        medicamento,
        tipo,
        status,
        dias_atras,
        dispensador=None):
    marcador = '[DEMO APRESENTACAO]'
    receita = Receita.query.filter(
        Receita.paciente_id == paciente.id,
        Receita.medico_id == medico.id,
        Receita.medicamento_id == medicamento.id,
        Receita.observacoes.like(f'%{marcador}%'),
    ).first()
    if not receita:
        receita = Receita(
            paciente_id=paciente.id,
            medico_id=medico.id,
            medicamento_id=medicamento.id,
        )
        db.session.add(receita)

    receita.tipo_receita = tipo
    receita.status = status
    receita.observacoes = f'{marcador} Orientação de uso registrada para demonstração.'
    receita.data_emissao = agora() - timedelta(days=dias_atras)
    receita.dispensada_por_id = dispensador.id if dispensador and status == 'dispensada' else None
    receita.dispensada_em = agora() - timedelta(days=max(dias_atras - 1, 0)
                                                ) if status == 'dispensada' else None
    return receita


def criar_log(usuario, acao, detalhes, dias_atras):
    existente = LogAtividade.query.filter_by(
        acao=acao, detalhes=detalhes).first()
    if existente:
        existente.usuario_id = usuario.id if usuario else None
        existente.created_at = agora() - timedelta(days=dias_atras)
        return existente

    log = LogAtividade(
        usuario_id=usuario.id if usuario else None,
        acao=acao,
        detalhes=detalhes,
        ip='127.0.0.1',
        created_at=agora() - timedelta(days=dias_atras),
    )
    db.session.add(log)
    return log


def limpar_registros_demo():
    Receita.query.filter(
        Receita.observacoes.like('%[DEMO APRESENTACAO]%')
        | Receita.observacoes.like('%Teste real demo%')
    ).delete(synchronize_session=False)

    demo_cpfs = [dados['cpf'] for dados in USUARIOS]
    demo_usuarios = Usuario.query.filter(Usuario.cpf.in_(demo_cpfs)).all()
    demo_usuario_ids = [usuario.id for usuario in demo_usuarios]

    demo_lotes = [dados['lote'] for dados in MEDICAMENTOS]
    demo_medicamentos = Medicamento.query.filter(
        Medicamento.lote.in_(demo_lotes)).all()
    demo_medicamento_ids = [
        medicamento.id for medicamento in demo_medicamentos]

    if demo_usuario_ids or demo_medicamento_ids:
        query = Doacao.query
        filtros = []
        if demo_usuario_ids:
            filtros.append(Doacao.usuario_id.in_(demo_usuario_ids))
        if demo_medicamento_ids:
            filtros.append(Doacao.medicamento_id.in_(demo_medicamento_ids))
        if filtros:
            from sqlalchemy import or_
            query.filter(or_(*filtros)).delete(synchronize_session=False)

    LogAtividade.query.filter(
        LogAtividade.acao.in_([
            'Seed Demo',
            'Recebimento de Doação',
            'Auditoria de Lotes',
            'Emissão de Receita',
        ])
    ).delete(synchronize_session=False)
    db.session.commit()


def main():
    app = create_app()
    with app.app_context():
        limpar_registros_demo()

        usuarios = {dados['cargo']: upsert_usuario(
            dados) for dados in USUARIOS}
        db.session.commit()

        medicamentos = {dados['nome']: upsert_medicamento(
            dados) for dados in MEDICAMENTOS}
        pacientes = {
            cpf: upsert_paciente(
                *
                dados) for dados in PACIENTES for cpf in [
                dados[1]]}
        medicos = {crm: upsert_medico(*dados)
                   for dados in MEDICOS for crm in [dados[1]]}
        farmacias = [upsert_farmacia(*dados) for dados in FARMACIAS]
        db.session.commit()

        criar_doacao(
            usuarios['Voluntário'],
            medicamentos['Dipirona 500mg'],
            40,
            6)
        criar_doacao(
            usuarios['Operador'],
            medicamentos['Paracetamol 750mg'],
            25,
            4)
        criar_doacao(
            usuarios['Farmacêutico'],
            medicamentos['Amoxicilina 500mg'],
            18,
            2)
        criar_doacao(
            usuarios['Voluntário'],
            medicamentos['Losartana 50mg'],
            30,
            1)
        # Doações adicionais para demonstração mais rica
        criar_doacao(
            usuarios['Médico'],
            medicamentos['Metformina 850mg'],
            50,
            3)
        criar_doacao(
            usuarios['Voluntário'],
            medicamentos['Ácido Fólico 5mg'],
            100,
            5)
        criar_doacao(
            usuarios['Operador'],
            medicamentos['Vitamina D3 2000UI'],
            75,
            7)
        criar_doacao(
            usuarios['Farmacêutico'],
            medicamentos['Aspirina 100mg'],
            60,
            10)
        criar_doacao(
            usuarios['Voluntário'],
            medicamentos['Captopril 25mg'],
            40,
            15)
        criar_doacao(
            usuarios['Operador'],
            medicamentos['Diazepam 10mg'],
            20,
            8)

        criar_receita(
            pacientes['10120230344'],
            medicos['CRM-SP 135790'],
            medicamentos['Losartana 50mg'],
            'Receita de Controle Especial (Branca)',
            'dispensada',
            8,
            usuarios['Farmacêutico'],
        )
        criar_receita(
            pacientes['20230340455'],
            medicos['CRM-SP 118245'],
            medicamentos['Amoxicilina 500mg'],
            'Receita de Controle Especial (Branca)',
            'pendente',
            2,
        )
        criar_receita(
            pacientes['40450560677'],
            medicos['CRM-SP 135790'],
            medicamentos['Clonazepam 0,5mg'],
            "Receita 'B' Especial (Azul)",
            'pendente',
            1,
        )
        # Receitas adicionais para demonstração mais rica
        criar_receita(
            pacientes['50560670788'],
            medicos['CRM-SP 156789'],
            medicamentos['Diazepam 10mg'],
            "Receita 'B' Especial (Azul)",
            'dispensada',
            12,
            usuarios['Farmacêutico'],
        )
        criar_receita(
            pacientes['60670780899'],
            medicos['CRM-SP 167890'],
            medicamentos['Metformina 850mg'],
            'Receita de Controle Especial (Branca)',
            'pendente',
            5,
        )
        criar_receita(
            pacientes['70780890900'],
            medicos['CRM-SP 135790'],
            medicamentos['Captopril 25mg'],
            'Receita de Controle Especial (Branca)',
            'dispensada',
            20,
            usuarios['Farmacêutico'],
        )
        criar_receita(
            pacientes['80890901011'],
            medicos['CRM-SP 156789'],
            medicamentos['Risperidona 2mg'],
            'Tarja Amarela',
            'pendente',
            3,
        )
        criar_receita(
            pacientes['90901011122'],
            medicos['CRM-SP 142680'],
            medicamentos['Insulina NPH 100 UI/mL'],
            'Receita de Controle Especial (Branca)',
            'pendente',
            1,
        )
        criar_receita(
            pacientes['01011121233'],
            medicos['CRM-SP 118245'],
            medicamentos['Ácido Fólico 5mg'],
            'Receita Simples',
            'dispensada',
            15,
            usuarios['Farmacêutico'],
        )

        criar_log(
            usuarios['Admin'],
            'Seed Demo',
            'Base de apresentação preparada com dados fictícios.',
            0)
        criar_log(
            usuarios['Operador'],
            'Recebimento de Doação',
            'Receptor registrou entrada de medicamentos demo.',
            1)
        criar_log(
            usuarios['Farmacêutico'],
            'Auditoria de Lotes',
            'Farmacêutico revisou vencimentos e controlados demo.',
            1)
        criar_log(usuarios['Médico'], 'Emissão de Receita',
                  'Médico emitiu prescrição demo para paciente.', 2)
        db.session.commit()

        print('Base demo preparada com sucesso.')
        print()
        print('Credenciais de apresentação:')
        print('  Admin        | CPF 00000000000 | senha admin123')
        print(f'  Voluntário   | CPF 22244466671 | senha {SENHA_DEMO}')
        print(f'  Farmacêutico | CPF 33355577782 | senha {SENHA_DEMO}')
        print(f'  Médico       | CPF 44466688893 | senha {SENHA_DEMO}')
        print(f'  Receptor     | CPF 55577799902 | senha {SENHA_DEMO}')
        print()
        print(
            f'Itens cadastrados: {
                len(usuarios)} usuários, {
                len(medicamentos)} medicamentos, ' f'{
                len(pacientes)} pacientes, {
                    len(medicos)} médicos, {
                        len(farmacias)} farmácias.')


if __name__ == '__main__':
    main()
