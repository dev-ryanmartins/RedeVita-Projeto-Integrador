from flask import Blueprint, render_template, request
from flask_login import login_required
from app.models.medicamento import Medicamento
from app.models.paciente import Paciente
from app.models.medico import Medico
from app.models.farmacia import Farmacia
from app.models.medicamento_referencia import MedicamentoReferencia

busca_bp = Blueprint("busca", __name__)

# Cache em memória para lookup O(1) (Hash Table)
_busca_cache = {
    'medicamentos': {},
    'principios_ativos': {},
    'referencias': {},
    'pacientes': {},
    'medicos': {},
    'farmacias': {},
    'last_update': None
}


def _atualizar_cache_busca():
    """
    Atualiza o cache de busca em memória.
    Constrói dicionários para lookup O(1) por princípio ativo e referências.
    """
    global _busca_cache
    
    try:
        # Cache de medicamentos por nome e princípio ativo
        medicamentos = Medicamento.query.all()
        _busca_cache['medicamentos'] = {
            med.nome.lower(): med for med in medicamentos
        }
        _busca_cache['principios_ativos'] = {
            med.principio_ativo.lower(): med 
            for med in medicamentos 
            if med.principio_ativo
        }
    except Exception:
        _busca_cache['medicamentos'] = {}
        _busca_cache['principios_ativos'] = {}
    
    try:
        # Cache de referências para lookup rápido
        referencias = MedicamentoReferencia.query.all()
        _busca_cache['referencias'] = {
            ref.nome_comercial.lower(): ref for ref in referencias
        }
    except Exception:
        _busca_cache['referencias'] = {}
    
    try:
        # Cache de pacientes
        pacientes = Paciente.query.all()
        _busca_cache['pacientes'] = {
            pac.nome.lower(): pac for pac in pacientes
        }
    except Exception:
        _busca_cache['pacientes'] = {}
    
    try:
        # Cache de médicos
        medicos = Medico.query.all()
        _busca_cache['medicos'] = {
            med.nome.lower(): med for med in medicos
        }
    except Exception:
        _busca_cache['medicos'] = {}
    
    try:
        # Cache de farmácias
        farmacias = Farmacia.query.all()
        _busca_cache['farmacias'] = {
            farm.nome_fantasia.lower(): farm for farm in farmacias
        }
    except Exception:
        _busca_cache['farmacias'] = {}
    
    from datetime import datetime
    _busca_cache['last_update'] = datetime.utcnow()


def _busca_cache_valido(max_age_minutes: int = 5) -> bool:
    """
    Verifica se o cache ainda é válido.
    """
    if _busca_cache['last_update'] is None:
        return False
    
    from datetime import datetime, timedelta
    idade = datetime.utcnow() - _busca_cache['last_update']
    return idade < timedelta(minutes=max_age_minutes)


@busca_bp.route("/buscar")
@login_required
def buscar():
    q = request.args.get("q", "").strip()
    medicamentos = []
    pacientes = []
    medicos = []
    farmacias = []

    if len(q) >= 2:
        # Atualiza cache se necessário (lazy loading)
        if not _busca_cache_valido():
            _atualizar_cache_busca()
        
        q_lower = q.lower()
        
        # Busca O(1) no cache para medicamentos por nome
        medicamentos_por_nome = [
            _busca_cache['medicamentos'].get(key)
            for key in _busca_cache['medicamentos']
            if q_lower in key
        ]
        medicamentos_por_nome = [m for m in medicamentos_por_nome if m is not None]
        
        # Busca O(1) no cache para medicamentos por princípio ativo
        medicamentos_por_principio = [
            _busca_cache['principios_ativos'].get(key)
            for key in _busca_cache['principios_ativos']
            if q_lower in key
        ]
        medicamentos_por_principio = [m for m in medicamentos_por_principio if m is not None]
        
        # Combina e remove duplicatas
        medicamentos_set = set(medicamentos_por_nome + medicamentos_por_principio)
        medicamentos = list(medicamentos_set)[:20]
        
        # Busca O(1) no cache para pacientes
        pacientes = [
            _busca_cache['pacientes'].get(key)
            for key in _busca_cache['pacientes']
            if q_lower in key
        ]
        pacientes = [p for p in pacientes if p is not None][:20]
        
        # Busca O(1) no cache para médicos
        medicos = [
            _busca_cache['medicos'].get(key)
            for key in _busca_cache['medicos']
            if q_lower in key
        ]
        medicos = [m for m in medicos if m is not None][:20]
        
        # Busca O(1) no cache para farmácias
        farmacias = [
            _busca_cache['farmacias'].get(key)
            for key in _busca_cache['farmacias']
            if q_lower in key
        ]
        farmacias = [f for f in farmacias if f is not None][:20]

    total = len(medicamentos) + len(pacientes) + len(medicos) + len(farmacias)
    return render_template(
        "busca.html",
        q=q,
        medicamentos=medicamentos,
        pacientes=pacientes,
        medicos=medicos,
        farmacias=farmacias,
        total=total,
    )
