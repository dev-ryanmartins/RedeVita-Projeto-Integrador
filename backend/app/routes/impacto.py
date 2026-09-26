from flask import Blueprint, render_template
from flask_login import login_required
from app.models.medicamento import Medicamento
from app.models.doacao import Doacao
from app.models.paciente import Paciente
from app.models.farmacia import Farmacia
from app.database import db
from app.core.decorators import equipe_clinica_required
from datetime import date

impacto_bp = Blueprint("impacto", __name__)


@impacto_bp.route("/impacto")
@login_required
@equipe_clinica_required
def impacto_social():
    """Calcula e exibe métricas de impacto social e sustentabilidade"""
    
    # Cálculos de impacto
    total_medicamentos = Medicamento.query.count()
    total_doacoes = Doacao.query.count()
    total_pacientes = Paciente.query.count()
    total_farmacias = Farmacia.query.count()
    
    # Estimativas baseadas em dados reais
    total_estoque = sum(m.quantidade for m in Medicamento.query.all())
    
    # Cálculo de impacto (estimativas conservadoras)
    # 1 unidade de medicamento = ~1 paciente beneficiado
    pacientes_beneficiados = total_doacoes + total_estoque
    
    # Estimativa de resíduos evitados (1 unidade = ~50g de resíduo evitado)
    residuos_evitados_kg = (total_doacoes + total_estoque) * 0.05
    
    # Medicamentos salvos (total - vencidos)
    medicamentos_vencidos = Medicamento.query.filter_by(status_semaforo=2).count()
    medicamentos_salvos = total_medicamentos - medicamentos_vencidos
    
    # Métricas mensais
    hoje = date.today()
    doacoes_mes = Doacao.query.filter(
        Doacao.data_doacao >= date(hoje.year, hoje.month, 1)
    ).count()
    
    return render_template(
        "impacto.html",
        total_medicamentos=total_medicamentos,
        total_doacoes=total_doacoes,
        total_pacientes=total_pacientes,
        total_farmacias=total_farmacias,
        total_estoque=total_estoque,
        pacientes_beneficiados=pacientes_beneficiados,
        residuos_evitados_kg=round(residuos_evitados_kg, 2),
        medicamentos_salvos=medicamentos_salvos,
        medicamentos_vencidos=medicamentos_vencidos,
        doacoes_mes=doacoes_mes
    )
