"""
Script de dados de apresentação do RedeVita.

Cria tabelas (se necessário) e popula o banco com dados ricos e coerentes em
português (contexto de saúde pública / Sorocaba-SP) para preencher TODAS as
telas do sistema durante uma apresentação.

Uso:
    python seed_apresentacao.py            # popula/atualiza (idempotente)
    python seed_apresentacao.py --reset    # limpa e repopula do zero

O script é idempotente: pode ser executado várias vezes sem duplicar os dados
principais (usa chaves naturais como CPF, CNPJ, CRM e (nome, lote)).
"""

import os
import sys
import unicodedata
from datetime import date, datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, 'backend')

for caminho in (BASE_DIR, BACKEND_DIR):
    if caminho not in sys.path:
        sys.path.insert(0, caminho)

from sqlalchemy.exc import IntegrityError

from backend.main import create_app
from app.database import db
from app.core.security import criptografar_senha

from app.models.usuario import Usuario
from app.models.farmacia import Farmacia
from app.models.instituicao import Instituicao
from app.models.medico import Medico
from app.models.paciente import Paciente
from app.models.medicamento import Medicamento
from app.models.medicamento_referencia import MedicamentoReferencia
from app.models.doacao import Doacao
from app.models.doacao_etapa import DoacaoEtapa, TipoEtapa, OrigemEvento
from app.models.movimento_estoque import MovimentoEstoque
from app.models.log_atividade import LogAtividade
from app.models.oferta_medicamento import OfertaMedicamento, StatusOferta
from app.models.reserva_oferta import ReservaOferta, StatusReserva
from app.models.necessidade_institucional import (
    NecessidadeInstitucional,
    StatusNecessidade,
    PrioridadeNecessidade,
)
from app.models.agendamento_entrega import AgendamentoEntrega, EstadoAgendamento
from app.models.receita import Receita
from app.models.receita_anexo import ReceitaAnexo
from app.models.aprovacao_farmaceutica import AprovacaoFarmaceutica, StatusAprovacao
from app.models.entrega_institucional import EntregaInstitucional, EstadoEntrega
from app.models.iot import (
    LeituraIoT,
    TagRFID,
    LoteTelemetria,
    ResultadoLoteEnum,
)
from app.models.perfil_resiliencia import (
    PerfilResilienciaFarmacia,
    SituacaoEnergiaEnum,
    SituacaoRefrigeracaoEnum,
    ApoioTemporarioEnum,
    PlanoContingenciaEnum,
    OrigemInformacaoEnum,
)
from app.models.campanha import Campanha
from app.utils.semaforo import calcular_status_semaforo


# ---------------------------------------------------------------------------
# Parâmetros de apresentação
# ---------------------------------------------------------------------------
DEMO_PASSWORD = "RedeVita@2026"
HOJE = date.today()
AGORA = datetime.utcnow()


def _norm(texto: str) -> str:
    """Normaliza texto (sem acentos, minúsculo) para comparação."""
    if not texto:
        return ""
    normalizado = unicodedata.normalize("NFKD", texto)
    normalizado = normalizado.encode("ascii", "ignore").decode("ascii")
    return " ".join(normalizado.lower().split())


def _cpf_valido(base: str) -> str:
    """Calcula os dígitos verificadores e retorna um CPF válido (11 dígitos)."""
    numeros = [int(d) for d in "".join(filter(str.isdigit, base))[:9]]
    while len(numeros) < 9:
        numeros.append(0)

    for peso_inicial in (10, 11):
        soma = sum(num * peso for num, peso in zip(numeros, range(peso_inicial, 1, -1)))
        digito = (soma * 10) % 11
        if digito == 10:
            digito = 0
        numeros.append(digito)

    return "".join(str(n) for n in numeros)


def _formatar_cpf(cpf: str) -> str:
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"


def _primeiro_ou_criar(modelo, filtros, **campos):
    """Busca por chave natural; cria se não existir; retorna (obj, criado).

    Idempotente por construção: se o registro já existir (pela chave natural)
    é reaproveitado. A inserção usa um SAVEPOINT para que, caso a chave natural
    informada não cubra alguma constraint UNIQUE (ex.: e-mail já usado por outro
    registro), o erro de chave duplicada seja absorvido sem abortar a transação
    externa — o script pode ser reexecutado quantas vezes for necessário.
    """
    obj = modelo.query.filter_by(**filtros).first()
    if obj:
        return obj, False
    obj = modelo(**campos)
    try:
        with db.session.begin_nested():
            db.session.add(obj)
    except IntegrityError:
        # Chave já existente: reaproveita o registro existente.
        obj = modelo.query.filter_by(**filtros).first()
        if obj is None:
            raise
        return obj, False
    return obj, True


def _ja_existe(modelo) -> bool:
    return db.session.query(modelo.query.exists()).scalar()


def resetar_banco(app):
    """Limpa o banco de apresentação para repopular do zero (flag --reset).

    Para SQLite, remove o arquivo físico (caminho mais rápido e sem resíduos).
    Para outros bancos (ex.: MySQL), recria o esquema via drop_all/create_all.
    """
    from sqlalchemy.engine import make_url

    with app.app_context():
        uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        url = make_url(uri)

        if url.get_backend_name() == "sqlite":
            caminho = url.database
            if caminho and caminho != ":memory:":
                if not os.path.isabs(caminho):
                    # SQLAlchemy resolve caminhos relativos a partir do cwd;
                    # mantemos um fallback para a raiz do projeto.
                    candidato = os.path.abspath(caminho)
                    if not os.path.exists(candidato):
                        alternativo = os.path.join(BASE_DIR, caminho)
                        if os.path.exists(alternativo):
                            candidato = alternativo
                    caminho = candidato
                db.session.remove()
                db.engine.dispose()
                if os.path.exists(caminho):
                    os.remove(caminho)
                    print(f"  Banco SQLite removido: {caminho}")
                else:
                    print(f"  Banco SQLite ainda não existia: {caminho}")
                return

        # Fallback genérico: recria todo o esquema do zero.
        db.session.remove()
        db.drop_all()
        db.create_all()
        print("  Esquema recriado (drop_all/create_all).")


# ---------------------------------------------------------------------------
# Seed principal
# ---------------------------------------------------------------------------
def popular(app):
    with app.app_context():
        # Garante que as tabelas existam (o create_app já roda create_all, mas
        # mantemos aqui por segurança ao rodar o script isoladamente).
        db.create_all()

        # Carrega referências ANVISA (populadas no startup) para decidir a tarja
        # correta de substâncias controladas (Portaria 344/98).
        referencias = MedicamentoReferencia.query.all()
        referencias_por_nome = {_norm(r.nome_comercial): r for r in referencias}
        principio_controlado = {
            _norm(r.principio_ativo): r
            for r in referencias
            if r.lista_portaria and r.principio_ativo
        }

        # ===================================================================
        # 1. USUÁRIOS E PERFIS
        # ===================================================================
        admin, _ = _primeiro_ou_criar(
            Usuario,
            {"cpf": _cpf_valido("111222333")},
            nome="Ana Administradora",
            cpf=_cpf_valido("111222333"),
            email="admin@redevita.demo",
            senha=criptografar_senha(DEMO_PASSWORD),
            cargo="Admin",
            ativo=True,
            senha_trocada=True,
        )

        # --- Farmácias / UBS (coordenadas reais de Sorocaba-SP) ---
        farmacia_ubs_central, _ = _primeiro_ou_criar(
            Farmacia,
            {"cnpj": "11.222.333/0001-81"},
            nome_fantasia="UBS Central Sorocaba",
            razao_social="Prefeitura Municipal de Sorocaba - UBS Central",
            cnpj="11.222.333/0001-81",
            endereco="Praça Coronel Fernando Prestes, 120 - Centro, Sorocaba - SP, 18010-060",
            responsavel="Dra. Patrícia Nogueira (Farm. Resp. CRF-SP 45.120)",
            latitude=-23.501530,
            longitude=-47.458060,
        )

        farmacia_popular_zoneamento, _ = _primeiro_ou_criar(
            Farmacia,
            {"cnpj": "22.333.444/0001-92"},
            nome_fantasia="Farmácia Popular do Éden",
            razao_social="RedeVita Farmácias Comunitárias LTDA",
            cnpj="22.333.444/0001-92",
            endereco="Av. Independência, 3050 - Éden, Sorocaba - SP, 18103-000",
            responsavel="Dr. Marcos Oliveira (Farm. Resp. CRF-SP 38.907)",
            latitude=-23.478510,
            longitude=-47.428120,
        )

        farmacia_central = farmacia_ubs_central
        farmacia_eden = farmacia_popular_zoneamento

        farm_user_1, _ = _primeiro_ou_criar(
            Usuario,
            {"cpf": _cpf_valido("222111333")},
            nome="Carla Farmacêutica",
            cpf=_cpf_valido("222111333"),
            email="farmacia1@redevita.demo",
            senha=criptografar_senha(DEMO_PASSWORD),
            cargo="Farmacêutico",
            ativo=True,
            senha_trocada=True,
            farmacia_id=farmacia_central.id,
        )

        farm_user_2, _ = _primeiro_ou_criar(
            Usuario,
            {"cpf": _cpf_valido("333111222")},
            nome="Roberto Farmacêutico",
            cpf=_cpf_valido("333111222"),
            email="farmacia2@redevita.demo",
            senha=criptografar_senha(DEMO_PASSWORD),
            cargo="Farmacêutico",
            ativo=True,
            senha_trocada=True,
            farmacia_id=farmacia_eden.id,
        )

        # --- Médicos ---
        medico_1, _ = _primeiro_ou_criar(
            Medico,
            {"crm": "CRM-SP 123456"},
            nome="Dr. João Pereira",
            crm="CRM-SP 123456",
            especialidade="Clínica Médica",
            contato="(15) 99876-1001",
        )
        medico_2, _ = _primeiro_ou_criar(
            Medico,
            {"crm": "CRM-SP 654321"},
            nome="Dra. Helena Souza",
            crm="CRM-SP 654321",
            especialidade="Cardiologia",
            contato="(15) 99876-1002",
        )

        medico_user_1, _ = _primeiro_ou_criar(
            Usuario,
            {"cpf": _cpf_valido("444555666")},
            nome="Dr. João Pereira",
            cpf=_cpf_valido("444555666"),
            email="medico1@redevita.demo",
            senha=criptografar_senha(DEMO_PASSWORD),
            cargo="Médico",
            ativo=True,
            senha_trocada=True,
        )
        medico_user_2, _ = _primeiro_ou_criar(
            Usuario,
            {"cpf": _cpf_valido("555666777")},
            nome="Dra. Helena Souza",
            cpf=_cpf_valido("555666777"),
            email="medico2@redevita.demo",
            senha=criptografar_senha(DEMO_PASSWORD),
            cargo="Médico",
            ativo=True,
            senha_trocada=True,
        )

        # --- Pacientes (entidades + logins de demonstração) ---
        pacientes_dados = [
            ("Maria Aparecida Lima", _cpf_valido("666777888"), date(1958, 4, 12), "(15) 99123-4001"),
            ("José Carlos Andrade", _cpf_valido("777888999"), date(1972, 9, 30), "(15) 99123-4002"),
            ("Fernanda Ribeiro Alves", _cpf_valido("888999000"), date(1990, 1, 22), "(15) 99123-4003"),
        ]
        pacientes = []
        for nome, cpf, nascimento, telefone in pacientes_dados:
            paciente, _ = _primeiro_ou_criar(
                Paciente,
                {"cpf": _formatar_cpf(cpf)},
                nome=nome,
                cpf=_formatar_cpf(cpf),
                data_nascimento=nascimento,
                endereco="Sorocaba - SP",
                telefone=telefone,
                email=f"paciente{len(pacientes) + 1}@email.demo",
            )
            pacientes.append(paciente)

            _primeiro_ou_criar(
                Usuario,
                {"cpf": cpf},
                nome=nome,
                cpf=cpf,
                email=f"paciente{len(pacientes)}@redevita.demo",
                senha=criptografar_senha(DEMO_PASSWORD),
                cargo="Paciente",
                ativo=True,
                senha_trocada=True,
            )

        # --- Instituições parceiras (entidades + logins) ---
        instituicao_1, _ = _primeiro_ou_criar(
            Instituicao,
            {"nome": "Lar São Vicente de Paulo"},
            nome="Lar São Vicente de Paulo",
            cnpj="33.444.555/0001-10",
            endereco="Rua da Penha, 980 - Centro, Sorocaba - SP",
            responsavel="Irmã Benedita Moraes",
            telefone="(15) 3231-4500",
            email="contato@larsaovicente.org.br",
            ativo=True,
        )
        instituicao_2, _ = _primeiro_ou_criar(
            Instituicao,
            {"nome": "Casa de Apoio Esperança"},
            nome="Casa de Apoio Esperança",
            cnpj="44.555.666/0001-21",
            endereco="Av. Comendador Pereira Inácio, 1500 - Vergueiro, Sorocaba - SP",
            responsavel="Sr. Antônio Ferraz",
            telefone="(15) 3222-7788",
            email="contato@casaesperanca.org.br",
            ativo=True,
        )

        _primeiro_ou_criar(
            Usuario,
            {"cpf": _cpf_valido("999000111")},
            nome="Instituição Lar São Vicente",
            cpf=_cpf_valido("999000111"),
            email="instituicao1@redevita.demo",
            senha=criptografar_senha(DEMO_PASSWORD),
            cargo="Instituição",
            ativo=True,
            senha_trocada=True,
            instituicao_id=instituicao_1.id,
        )
        _primeiro_ou_criar(
            Usuario,
            {"cpf": _cpf_valido("100200300")},
            nome="Instituição Casa Esperança",
            cpf=_cpf_valido("100200300"),
            email="instituicao2@redevita.demo",
            senha=criptografar_senha(DEMO_PASSWORD),
            cargo="Instituição",
            ativo=True,
            senha_trocada=True,
            instituicao_id=instituicao_2.id,
        )

        db.session.commit()

        # ===================================================================
        # 2. INVENTÁRIO E SEMÁFORO SANITÁRIO (>= 15 lotes)
        # ===================================================================
        # (nome, lote, dias_para_validade, quantidade, tarja, principio, uso_continuo)
        medicamentos_dados = [
            ("Dipirona 500mg", "DIP-2401", 400, 320, "Sem Tarja", "Dipirona Sódica", False),
            ("Paracetamol 500mg", "PAR-2402", 365, 210, "Sem Tarja", "Paracetamol", False),
            ("Ibuprofeno 400mg", "IBU-2403", 300, 150, "Tarja Vermelha", "Ibuprofeno", False),
            ("Omeprazol 20mg", "OME-2404", 250, 180, "Tarja Vermelha", "Omeprazol", True),
            ("Losartana Potássica 50mg", "LOS-2405", 420, 240, "Tarja Vermelha", "Losartana Potássica", True),
            ("Metformina 850mg", "MET-2406", 200, 300, "Tarja Vermelha", "Metformina", True),
            ("Amoxicilina 500mg", "AMO-2407", 90, 120, "Tarja Vermelha", "Amoxicilina", False),
            ("Sinvastatina 20mg", "SIN-2408", 365, 160, "Tarja Vermelha", "Sinvastatina", True),
            ("Clonazepam 2mg", "CLO-2409", 25, 60, "Portaria 344", "Clonazepam", True),
            ("Diazepam 10mg", "DIA-2410", 18, 40, "Portaria 344", "Diazepam", True),
            ("Tramadol 50mg", "TRA-2411", 10, 30, "Portaria 344", "Tramadol", True),
            ("Codeína + Paracetamol", "COD-2412", 5, 25, "Portaria 344", "Codeína", True),
            ("Esomeprazol 40mg", "ESO-2413", 0, 50, "Tarja Vermelha", "Esomeprazol", True),
            ("Prednisona 20mg", "PRE-2414", 0, 35, "Tarja Vermelha", "Prednisona", False),
            ("Insulina NPH 100UI", "INS-2415", 2, 20, "Tarja Vermelha", "Insulina Humana NPH", True),
            ("Metoclopramida 10mg", "MTC-2416", -20, 80, "Tarja Vermelha", "Metoclopramida", False),
            ("Ácido Acetilsalicílico 100mg", "AAS-2417", -45, 500, "Sem Tarja", "Ácido Acetilsalicílico", True),
            ("Salbutamol Spray", "SAL-2418", 180, 90, "Tarja Vermelha", "Salbutamol", True),
            ("Fluconazol 150mg", "FLU-2419", 120, 0, "Tarja Vermelha", "Fluconazol", False),
        ]

        medicamentos = []
        for nome, lote, dias_validade, quantidade, tarja, principio, uso_continuo in medicamentos_dados:
            data_validade = HOJE + timedelta(days=dias_validade)

            # Ajusta tarja e vínculo caso o princípio ativo seja controlado (Portaria 344).
            referencia = None
            if _norm(principio) in principio_controlado:
                referencia = principio_controlado[_norm(principio)]
                tarja = "Portaria 344"

            medicamento, _ = _primeiro_ou_criar(
                Medicamento,
                {"nome": nome, "lote": lote},
                nome=nome,
                lote=lote,
                data_validade=data_validade,
                quantidade=quantidade,
                status_semaforo=calcular_status_semaforo(data_validade),
                ativo=True,
                tarja=tarja,
                principio_ativo=principio,
                uso_continuo=uso_continuo,
                referencia_id=referencia.id if referencia else None,
                observacoes="Lote de demonstração - RedeVita",
            )
            medicamentos.append(medicamento)

        db.session.commit()

        # ===================================================================
        # 3. DOAÇÕES (diferentes etapas), MOVIMENTOS E LOGS
        # ===================================================================
        if not _ja_existe(Doacao):
            etapas_doador = [
                ("Concluída", "APROVADO", [TipoEtapa.REGISTRO_CRIADO, TipoEtapa.PESAGEM_REGISTRADA]),
                ("Aprovação farmacêutica", "EM_CONFERENCIA", [TipoEtapa.REGISTRO_CRIADO, TipoEtapa.CONFERENCIA_MANUAL_REQUERIDA]),
                ("Triagem", "PENDENTE", [TipoEtapa.REGISTRO_CRIADO]),
                ("Concluída", "APROVADO", [TipoEtapa.REGISTRO_CRIADO, TipoEtapa.PESAGEM_REGISTRADA, TipoEtapa.CONFERENCIA_MANUAL_CONCLUIDA]),
            ]
            for indice, (situacao, status_conferencia, etapas) in enumerate(etapas_doador):
                medicamento = medicamentos[indice % len(medicamentos)]
                quantidade = 5 + indice * 3
                doacao = Doacao(
                    usuario_id=(admin.id if indice % 2 == 0 else farm_user_1.id),
                    medicamento_id=medicamento.id,
                    data_doacao=AGORA - timedelta(days=15 - indice * 3),
                    quantidade=quantidade,
                    peso_gramas=round(quantidade * 0.5, 2),
                    status_conferencia=status_conferencia,
                    cancelado=False,
                )
                db.session.add(doacao)
                db.session.flush()

                for ordem, tipo in enumerate(etapas):
                    db.session.add(
                        DoacaoEtapa(
                            doacao_id=doacao.id,
                            tipo_etapa=tipo.value,
                            data_hora=doacao.data_doacao + timedelta(hours=ordem),
                            usuario_id=farm_user_1.id,
                            origem=OrigemEvento.USUARIO.value,
                            observacao=f"Etapa '{tipo.value}' registrada para demonstração.",
                        )
                    )
            db.session.commit()

        if not _ja_existe(MovimentoEstoque):
            for indice, medicamento in enumerate(medicamentos[:8]):
                db.session.add(
                    MovimentoEstoque(
                        medicamento_id=medicamento.id,
                        quantidade=10 + indice * 2,
                        tipo="ENTRADA_DOACAO",
                        operacao_id=f"MOV-ENTRADA-{medicamento.lote}",
                        usuario_id=farm_user_1.id,
                        autorizado_por_id=admin.id,
                        criado_em=AGORA - timedelta(days=10 - indice),
                        justificativa="Entrada de doação conferida.",
                        referencia_documento=f"DON-{1000 + indice}",
                    )
                )
            db.session.commit()

        # ===================================================================
        # 4. RECEITUÁRIO MÉDICO
        # ===================================================================
        if not _ja_existe(Receita):
            receitas_dados = [
                (pacientes[0], medico_1, medicamentos[3], "pendente", "Receita de Controle Especial (Branca)", None),
                (pacientes[1], medico_2, medicamentos[4], "dispensada", "Receita de Controle Especial (Branca)", farm_user_1.id),
                (pacientes[2], medico_1, medicamentos[8], "pendente", "Receita 'B' Especial (Azul) ou 'A' (Amarela)", None),
                (pacientes[0], medico_2, medicamentos[5], "dispensada", "Receita de Controle Especial (Branca)", farm_user_1.id),
            ]
            for indice, (paciente, medico, medicamento, status, tipo, dispensada_por) in enumerate(receitas_dados):
                receita = Receita(
                    paciente_id=paciente.id,
                    medico_id=medico.id,
                    medicamento_id=medicamento.id,
                    observacoes="Uso contínuo — acompanhamento mensal.",
                    data_emissao=AGORA - timedelta(days=indice),
                    tipo_receita=tipo,
                    status=status,
                    dispensada_em=(AGORA - timedelta(days=indice) + timedelta(hours=2)) if dispensada_por else None,
                    dispensada_por_id=dispensada_por,
                )
                db.session.add(receita)
            db.session.commit()

        # ===================================================================
        # 5. OFERTAS, RESERVAS, MATCHING E ENTREGAS INSTITUCIONAIS
        # ===================================================================
        if not _ja_existe(OfertaMedicamento):
            ofertas_def = [
                (farmacia_central, medicamentos[0], 100, 20, StatusOferta.DISPONIVEL.value),
                (farmacia_central, medicamentos[3], 50, 0, StatusOferta.DISPONIVEL.value),
                (farmacia_eden, medicamentos[4], 80, 30, StatusOferta.RESERVADA.value),
                (farmacia_eden, medicamentos[18], 60, 0, StatusOferta.DISPONIVEL.value),
            ]
            for farmacia, medicamento, ofertada, reservada, status in ofertas_def:
                db.session.add(
                    OfertaMedicamento(
                        farmacia_id=farmacia.id,
                        medicamento_id=medicamento.id,
                        quantidade_ofertada=ofertada,
                        quantidade_reservada=reservada,
                        status=status,
                        data_expiracao=AGORA + timedelta(days=30),
                        criado_por_id=farm_user_1.id,
                        criado_em=AGORA - timedelta(days=5),
                        observacoes="Oferta de demonstração para matching institucional.",
                    )
                )
            db.session.commit()

        ofertas = OfertaMedicamento.query.order_by(OfertaMedicamento.id).all()

        if not _ja_existe(NecessidadeInstitucional):
            necessidades_def = [
                (instituicao_1, medicamentos[3], "Omeprazol 20mg — uso contínuo de idosos", 120, PrioridadeNecessidade.ALTA.value, StatusNecessidade.REGISTRADA.value),
                (instituicao_2, medicamentos[0], "Dipirona 500mg", 200, PrioridadeNecessidade.URGENTE.value, StatusNecessidade.EM_REVISAO.value),
                (instituicao_1, medicamentos[5], "Metformina 850mg", 90, PrioridadeNecessidade.MEDIA.value, StatusNecessidade.RASCUNHO.value),
                (instituicao_2, medicamentos[4], "Losartana Potássica 50mg", 150, PrioridadeNecessidade.ALTA.value, StatusNecessidade.ENCERRADA.value),
            ]
            for instituicao, medicamento, descritivo, quantidade, prioridade, status in necessidades_def:
                db.session.add(
                    NecessidadeInstitucional(
                        instituicao_id=instituicao.id,
                        nome_instituicao=instituicao.nome,
                        medicamento_referencia_id=medicamento.referencia_id,
                        produto_descritivo=descritivo,
                        quantidade_solicitada=quantidade,
                        unidade="unidade",
                        data_desejada=HOJE + timedelta(days=15),
                        prioridade=prioridade,
                        status=status,
                        criado_por_id=admin.id,
                        criado_em=AGORA - timedelta(days=4),
                        observacoes="Necessidade cadastrada para demonstração.",
                    )
                )
            db.session.commit()

        # Reservas de ofertas (com fluxo farmacêutico, entrega e anexo de receita)
        if not _ja_existe(ReservaOferta) and ofertas:
            oferta_a = ofertas[0]
            reserva_1 = ReservaOferta(
                oferta_id=oferta_a.id,
                instituicao_id=instituicao_1.id,
                quantidade_reservada=20,
                status=StatusReserva.CONFIRMADA.value,
                reservado_por_id=admin.id,
                confirmado_por_id=farm_user_1.id,
                criado_em=AGORA - timedelta(days=3),
                confirmado_em=AGORA - timedelta(days=2),
                data_expiracao=AGORA + timedelta(days=20),
                observacoes="Reserva confirmada para o Lar São Vicente.",
                operacao_id="RES-DEMO-001",
            )
            oferta_b = ofertas[1] if len(ofertas) > 1 else ofertas[0]
            reserva_2 = ReservaOferta(
                oferta_id=oferta_b.id,
                instituicao_id=instituicao_2.id,
                quantidade_reservada=15,
                status=StatusReserva.DESPACHADA.value,
                reservado_por_id=admin.id,
                confirmado_por_id=farm_user_1.id,
                criado_em=AGORA - timedelta(days=6),
                confirmado_em=AGORA - timedelta(days=5),
                data_expiracao=AGORA + timedelta(days=10),
                observacoes="Reserva despachada para a Casa Esperança.",
                operacao_id="RES-DEMO-002",
            )
            oferta_c = ofertas[2] if len(ofertas) > 2 else ofertas[0]
            reserva_3 = ReservaOferta(
                oferta_id=oferta_c.id,
                instituicao_id=instituicao_1.id,
                quantidade_reservada=10,
                status=StatusReserva.RESERVADA.value,
                reservado_por_id=admin.id,
                criado_em=AGORA - timedelta(days=1),
                data_expiracao=AGORA + timedelta(days=14),
                observacoes="Reserva aguardando aprovação farmacêutica.",
                operacao_id="RES-DEMO-003",
            )
            db.session.add_all([reserva_1, reserva_2, reserva_3])
            db.session.flush()

            db.session.add(
                AprovacaoFarmaceutica(
                    reserva_id=reserva_1.id,
                    usuario_id=farm_user_1.id,
                    status=StatusAprovacao.APROVADA.value,
                    observacoes="Aprovação farmacêutica após conferência de lote e validade.",
                    criado_em=AGORA - timedelta(days=2),
                    operacao_id="APR-DEMO-001",
                )
            )

            db.session.add(
                ReceitaAnexo(
                    reserva_id=reserva_2.id,
                    nome_arquivo_original="receita_controlada_demo.pdf",
                    nome_arquivo_interno="receita_controlada_demo_8f3a.pdf",
                    caminho_arquivo="uploads/demo/receita_controlada_demo_8f3a.pdf",
                    tamanho_bytes=184320,
                    tipo_mime="application/pdf",
                    validado=True,
                    uploadado_por_id=farm_user_1.id,
                    uploadado_em=AGORA - timedelta(days=5),
                    observacoes="Receita digitalizada validada (demonstração).",
                )
            )

            db.session.add(
                EntregaInstitucional(
                    reserva_id=reserva_2.id,
                    estado=EstadoEntrega.DESPACHADA.value,
                    despachado_por_id=farm_user_1.id,
                    despachado_em=AGORA - timedelta(days=4),
                    observacoes="Entrega despachada — aguardando confirmação de recebimento.",
                    operacao_id="ENT-DEMO-001",
                    criado_em=AGORA - timedelta(days=5),
                )
            )
            db.session.commit()

        # ===================================================================
        # 6. AGENDAMENTOS DE ENTREGA
        # ===================================================================
        if not _ja_existe(AgendamentoEntrega):
            agendamentos_def = [
                (farmacia_central, farmacia_eden, EstadoAgendamento.CONFIRMADO.value, 2),
                (farmacia_eden, farmacia_central, EstadoAgendamento.PROPOSTA.value, 4),
                (farmacia_central, farmacia_eden, EstadoAgendamento.AGUARDANDO_DESTINO.value, 6),
            ]
            for origem, destino, estado, dias in agendamentos_def:
                inicio = AGORA + timedelta(days=dias)
                db.session.add(
                    AgendamentoEntrega(
                        farmacia_origem_id=origem.id,
                        farmacia_destino_id=destino.id,
                        data_hora_inicio=inicio,
                        data_hora_fim=inicio + timedelta(hours=2),
                        estado=estado,
                        criado_por_id=admin.id,
                        criado_em=AGORA - timedelta(days=1),
                        observacoes="Transferência programada entre unidades (demonstração).",
                    )
                )
            db.session.commit()

        # ===================================================================
        # 7. CAMPANHAS
        # ===================================================================
        if not _ja_existe(Campanha):
            campanhas_def = [
                ("Campanha do Agasalho + Medicamentos", "Arrecadação de medicamentos de uso contínuo para idosos em situação de vulnerabilidade.", "arrecadacao", "ativa"),
                ("Alerta de Vencimento — Julho", "Lotes próximos do vencimento precisam de destinação adequada.", "alerta", "ativa"),
                ("Uso Racional de Medicamentos", "Informativo para a comunidade sobre descarte e uso correto.", "informativo", "concluida"),
            ]
            for indice, (titulo, descricao, tipo, status) in enumerate(campanhas_def):
                db.session.add(
                    Campanha(
                        titulo=titulo,
                        descricao=descricao,
                        tipo=tipo,
                        data_inicio=HOJE - timedelta(days=10 + indice * 5),
                        data_fim=HOJE + timedelta(days=30),
                        status=status,
                        criador_id=admin.id,
                        created_at=AGORA - timedelta(days=10 + indice * 5),
                    )
                )
            db.session.commit()

        # ===================================================================
        # 8. MONITORAMENTO IoT E CADEIA DE FRIO (telemetria persistida)
        # ===================================================================
        if not _ja_existe(LeituraIoT):
            _gerar_telemetria(farmacia_central, farmacia_eden)

        if not _ja_existe(LoteTelemetria):
            _gerar_lotes_telemetria(farmacia_central, farmacia_eden)

        if not _ja_existe(TagRFID):
            db.session.add_all([
                TagRFID(
                    tag_uid="a3f1" * 16,
                    usuario_id=farm_user_1.id,
                    descricao="Crachá Farmacêutica — UBS Central",
                    ativo=True,
                    data_cadastro=AGORA - timedelta(days=30),
                    ultimo_acesso=AGORA - timedelta(hours=2),
                ),
                TagRFID(
                    tag_uid="b7c2" * 16,
                    usuario_id=admin.id,
                    descricao="Crachá Administrador",
                    ativo=True,
                    data_cadastro=AGORA - timedelta(days=60),
                    ultimo_acesso=AGORA - timedelta(days=1),
                ),
            ])
            db.session.commit()

        # ===================================================================
        # 9. PERFIL DE RESILIÊNCIA DAS FARMÁCIAS
        # ===================================================================
        _garantir_perfil_resiliencia(farmacia_central, admin.id)
        _garantir_perfil_resiliencia(farmacia_eden, admin.id)

        # ===================================================================
        # 10. LOGS DE AUDITORIA
        # ===================================================================
        if not _ja_existe(LogAtividade):
            _gerar_logs(admin, farm_user_1, medico_user_1)

        _imprimir_credenciais()


# ---------------------------------------------------------------------------
# Geração de telemetria IoT (gráficos, radar de integridade, cadeia de frio)
# ---------------------------------------------------------------------------
def _gerar_telemetria(farmacia_central, farmacia_eden):
    dispositivos = [
        ("ESP32-UBS-CENTRAL-REF", farmacia_central.id),
        ("ESP32-FARM-EDEN-REF", farmacia_eden.id),
    ]
    inicio = AGORA - timedelta(days=4)
    total_leituras = 0

    for dispositivo_id, farmacia_id in dispositivos:
        # Série horária normal, com uma lacuna proposital (para o Radar detectar).
        for hora in range(0, 97):
            if 40 <= hora <= 45:
                continue  # lacuna de ~6h
            data_hora = inicio + timedelta(hours=hora)
            temperatura = round(2 + 3 * (hora % 5) / 5 + (hora % 3) * 0.4, 2)  # 2 a ~6°C
            umidade = round(45 + (hora % 7), 2)
            db.session.add(
                LeituraIoT(
                    dispositivo_id=dispositivo_id,
                    farmacia_id=farmacia_id,
                    temperatura=temperatura,
                    umidade=umidade,
                    luminosidade_lux=round(120 + (hora % 30), 2),
                    data_hora=data_hora,
                )
            )
            total_leituras += 1

        # Picos térmicos (excursão) para os alertas e gráficos.
        for offset, temperatura in ((-36, 25.8), (-12, 31.5)):
            db.session.add(
                LeituraIoT(
                    dispositivo_id=dispositivo_id,
                    farmacia_id=farmacia_id,
                    temperatura=temperatura,
                    umidade=78.0,
                    luminosidade_lux=140.0,
                    data_hora=inicio + timedelta(hours=96 + offset) if offset < 0 else AGORA,
                )
            )
            total_leituras += 1

        # Leitura duplicada (candidato a duplicidade no Radar).
        data_dup = AGORA - timedelta(days=1) - timedelta(minutes=30)
        for _ in range(2):
            db.session.add(
                LeituraIoT(
                    dispositivo_id=dispositivo_id,
                    farmacia_id=farmacia_id,
                    temperatura=4.2,
                    umidade=50.0,
                    luminosidade_lux=130.0,
                    data_hora=data_dup,
                )
            )
            total_leituras += 1

        # Leitura com timestamp no futuro (gap de sincronização).
        db.session.add(
            LeituraIoT(
                dispositivo_id=dispositivo_id,
                farmacia_id=farmacia_id,
                temperatura=5.0,
                umidade=52.0,
                luminosidade_lux=128.0,
                data_hora=AGORA + timedelta(minutes=25),
            )
        )
        total_leituras += 1

    db.session.commit()
    print(f"  Telemetria IoT: {total_leituras} leituras geradas para 2 dispositivos.")


def _gerar_lotes_telemetria(farmacia_central, farmacia_eden):
    lotes_def = [
        ("ESP32-UBS-CENTRAL-REF", 120, 120, 0, ResultadoLoteEnum.COMPLETO, 1, None),
        ("ESP32-FARM-EDEN-REF", 96, 94, 2, ResultadoLoteEnum.PARCIAL, 1, {"umidade_invalida": 2}),
        ("ESP32-UBS-CENTRAL-REF", 60, 45, 15, ResultadoLoteEnum.PARCIAL, 2, {"timestamp_invalido": 10, "valor_ausente": 5}),
        ("ESP32-FARM-EDEN-REF", 30, 0, 30, ResultadoLoteEnum.REJEITADO, 1, {"payload_corrompido": 30}),
        ("ESP32-UBS-CENTRAL-REF", 144, 144, 0, ResultadoLoteEnum.COMPLETO, 1, None),
        ("ESP32-FARM-EDEN-REF", 72, 70, 2, ResultadoLoteEnum.PARCIAL, 1, {"temperatura_fora_faixa": 2}),
    ]
    for indice, (dispositivo, recebidas, processadas, rejeitadas, resultado, qtd_disp, erros) in enumerate(lotes_def):
        db.session.add(
            LoteTelemetria(
                lote_id=f"lote-demo-{indice + 1:04d}-8f3a",
                data_recebimento=AGORA - timedelta(days=indice, hours=indice),
                total_recebidas=recebidas,
                total_processadas=processadas,
                total_rejeitadas=rejeitadas,
                resultado=resultado,
                qtd_dispositivos=qtd_disp,
                dispositivo_principal=dispositivo,
                erros_por_categoria=erros,
            )
        )
    db.session.commit()
    print(f"  Diagnóstico IoT: {len(lotes_def)} lotes de telemetria gerados.")


def _garantir_perfil_resiliencia(farmacia, usuario_id):
    existente = PerfilResilienciaFarmacia.query.filter_by(farmacia_id=farmacia.id).first()
    if existente:
        return
    db.session.add(
        PerfilResilienciaFarmacia(
            farmacia_id=farmacia.id,
            situacao_energia=SituacaoEnergiaEnum.DISPONIVEL,
            situacao_refrigeracao=SituacaoRefrigeracaoEnum.DISPONIVEL,
            apoio_temporario=ApoioTemporarioEnum.SIM,
            plano_contingencia=PlanoContingenciaEnum.EXISTENTE,
            data_ultima_verificacao=AGORA - timedelta(days=15),
            data_prevista_revisao=AGORA + timedelta(days=75),
            origem_informacao=OrigemInformacaoEnum.VERIFICADA,
            usuario_responsavel_id=usuario_id,
            criado_em=AGORA - timedelta(days=15),
        )
    )
    db.session.commit()


def _gerar_logs(admin, farm_user, medico_user):
    acoes = [
        (admin, "Login", 'Usuário "Ana Administradora" (Admin) fez login — IP: 10.0.0.10'),
        (farm_user, "CADASTRO_MEDICAMENTO", "Cadastro do lote DIP-2401 (Dipirona 500mg)."),
        (farm_user, "TRIAGEM_DOACAO", "Triagem de doação conferida e aprovada."),
        (medico_user, "EMISSAO_RECEITA", "Receita emitida para Maria Aparecida Lima."),
        (admin, "EXCLUSAO_MEDICAMENTO", "Exclusão lógica de lote vencido AAS-2417."),
        (farm_user, "BAIXA_ESTOQUE", "Baixa de estoque por dispensação — 10 unidades."),
        (admin, "APROVACAO_FARMACEUTICA", "Aprovação farmacêutica da reserva RES-DEMO-001."),
        (farm_user, "ALERTA_TÉRMICO_CRÍTICO", "Sensor ESP32-UBS-CENTRAL-REF registrou 31.5°C."),
        (admin, "Redefinição de Senha", "Redefinição de senha do usuário de demonstração."),
        (farm_user, "Login", 'Usuário "Carla Farmacêutica" (Farmacêutico) fez login — IP: 10.0.0.22'),
    ]
    for indice, (usuario, acao, detalhes) in enumerate(acoes):
        db.session.add(
            LogAtividade(
                usuario_id=usuario.id,
                acao=acao,
                detalhes=detalhes,
                ip="10.0.0." + str(10 + indice),
                created_at=AGORA - timedelta(hours=indice * 3),
            )
        )
    db.session.commit()


# ---------------------------------------------------------------------------
# Impressão das credenciais
# ---------------------------------------------------------------------------
def _imprimir_credenciais():
    linha = "=" * 96
    print("\n" + linha)
    print("  RedeVita — CREDENCIAIS DE APRESENTAÇÃO (ambiente de demonstração)")
    print(linha)
    print(f"  {'PERFIL':<14}{'E-MAIL':<34}{'CPF':<14}{'SENHA':<16}")
    print("-" * 96)

    credenciais = [
        ("Admin", "admin@redevita.demo"),
        ("Farmácia", "farmacia1@redevita.demo"),
        ("Farmácia", "farmacia2@redevita.demo"),
        ("Médico", "medico1@redevita.demo"),
        ("Médico", "medico2@redevita.demo"),
        ("Paciente", "paciente1@redevita.demo"),
        ("Paciente", "paciente2@redevita.demo"),
        ("Paciente", "paciente3@redevita.demo"),
        ("Instituição", "instituicao1@redevita.demo"),
        ("Instituição", "instituicao2@redevita.demo"),
    ]

    for perfil, email in credenciais:
        usuario = Usuario.query.filter_by(email=email).first()
        cpf = usuario.cpf if usuario else "-"
        print(f"  {perfil:<14}{email:<34}{cpf:<14}{DEMO_PASSWORD:<16}")

    print("-" * 96)
    print("  Senha única de demonstração para todos os perfis:", DEMO_PASSWORD)
    print("  Dica: na tela de login use 'Preencher credenciais' (autofill) ou")
    print("        'Acesso rápido (demonstração)' para trocar de perfil em um clique.")
    print(linha)

    # Estatísticas rápidas para conferência
    print("  Resumo dos dados:")
    print(f"    Medicamentos: {Medicamento.query.count()} | "
          f"Vencidos/Vermelhos: {Medicamento.query.filter(Medicamento.status_semaforo == 2).count()} | "
          f"Próximos do vencimento: {Medicamento.query.filter(Medicamento.status_semaforo == 1).count()}")
    print(f"    Farmácias: {Farmacia.query.count()} | Médicos: {Medico.query.count()} | "
          f"Pacientes: {Paciente.query.count()} | Instituições: {Instituicao.query.count()}")
    print(f"    Doações: {Doacao.query.count()} | Receitas: {Receita.query.count()} | "
          f"Ofertas: {OfertaMedicamento.query.count()} | Reservas: {ReservaOferta.query.count()}")
    print(f"    Telemetria IoT: {LeituraIoT.query.count()} | Lotes: {LoteTelemetria.query.count()} | "
          f"Logs: {LogAtividade.query.count()}")
    print(linha + "\n")


if __name__ == "__main__":
    reset = "--reset" in sys.argv[1:]
    aplicacao = create_app()
    if reset:
        print("\n[--reset] Limpando o banco de apresentação antes de repopular...")
        resetar_banco(aplicacao)
    print("\nPopulando o banco de apresentação do RedeVita...")
    print(f"Banco em uso: {aplicacao.config['SQLALCHEMY_DATABASE_URI']}\n")
    popular(aplicacao)
    print("Concluído com sucesso!")
