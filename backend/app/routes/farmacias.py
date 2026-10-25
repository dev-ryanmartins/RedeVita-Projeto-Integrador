from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models.farmacia import Farmacia
from app.database import db
from app.core.decorators import (
    admin_required,
    farmaceutico_required,
    equipe_clinica_required,
)
from app.utils.log_helper import registrar_log
from app.utils.validators import sanitizar_input_string, detectar_padroes_suspeitos
from app.utils.document_validation import validar_cnpj
from app.core.decorators import audit_critical_action
import re
import math

farmacias_bp = Blueprint("farmacias", __name__)

_MAX_NOME = 150
_MAX_CNPJ_RAW = 30
_MAX_END = 255
_MAX_RESP = 150


def _limpar_cnpj(cnpj: str) -> str:
    return re.sub(r"\D", "", cnpj)


def _validar_coordenada(latitude: str, longitude: str) -> tuple[bool, str]:
    """
    Valida coordenadas geográficas fornecidas como strings.
    
    Args:
        latitude: Latitude como string
        longitude: Longitude como string
    
    Returns:
        Tuple (valido, mensagem_erro)
    """
    # Se vazias, são opcionais (válido)
    if not latitude and not longitude:
        return True, ""
    
    # Se uma fornecida, ambas devem ser fornecidas
    if (latitude and not longitude) or (not latitude and longitude):
        return False, "Forneça latitude e longitude, ou deixe ambos vazios"
    
    # Tentar converter para float
    try:
        lat = float(latitude)
        lon = float(longitude)
    except (TypeError, ValueError):
        return False, "Latitude e longitude devem ser números válidos"
    
    # Verificar NaN ou infinito
    if math.isnan(lat) or math.isnan(lon):
        return False, "Coordenadas não podem ser NaN"
    if math.isinf(lat) or math.isinf(lon):
        return False, "Coordenadas não podem ser infinitas"
    
    # Verificar intervalos geográficos
    if not (-90 <= lat <= 90):
        return False, f"Latitude deve estar entre -90 e 90 (recebido: {lat})"
    if not (-180 <= lon <= 180):
        return False, f"Longitude deve estar entre -180 e 180 (recebido: {lon})"
    
    return True, ""


def _validar_campos_farmacia(nome_fantasia, cnpj_raw, endereco, responsavel, latitude=None, longitude=None):
    if not nome_fantasia or not cnpj_raw or not endereco or not responsavel:
        return "Preencha todos os campos obrigatórios."
    if len(nome_fantasia) > _MAX_NOME:
        return f"Nome fantasia muito longo (máx. {_MAX_NOME} caracteres)."
    if len(endereco) > _MAX_END:
        return f"Endereço muito longo (máx. {_MAX_END} caracteres)."
    if len(responsavel) > _MAX_RESP:
        return f"Nome do responsável muito longo (máx. {_MAX_RESP} caracteres)."
    
    # Validar coordenadas se fornecidas
    if latitude is not None or longitude is not None:
        valido, erro = _validar_coordenada(latitude or "", longitude or "")
        if not valido:
            return erro
    
    return None


@farmacias_bp.route("/farmacias")
@login_required
@equipe_clinica_required
def listar_farmacias():
    try:
        farmacias = Farmacia.query.order_by(Farmacia.id.desc()).all()
    except Exception:
        farmacias = []
    return render_template("farmacias.html", farmacias=farmacias)


@farmacias_bp.route("/farmacia/nova", methods=["POST"])
@login_required
@farmaceutico_required
def nova_farmacia():
    nome_fantasia = sanitizar_input_string(request.form.get("nome_fantasia", ""), max_length=_MAX_NOME)
    razao_social = sanitizar_input_string(request.form.get("razao_social", ""), max_length=_MAX_NOME)
    cnpj_raw = request.form.get("cnpj", "").strip()[:_MAX_CNPJ_RAW]
    endereco = sanitizar_input_string(request.form.get("endereco", ""), max_length=_MAX_END)
    responsavel = sanitizar_input_string(request.form.get("responsavel", ""), max_length=_MAX_RESP)
    latitude = request.form.get("latitude", "").strip()
    longitude = request.form.get("longitude", "").strip()

    # Detecta padrões suspeitos
    if detectar_padroes_suspeitos(nome_fantasia) or detectar_padroes_suspeitos(endereco) or detectar_padroes_suspeitos(responsavel):
        flash("Entrada contém caracteres não permitidos.", "danger")
        return redirect(url_for("farmacias.listar_farmacias"))

    erro = _validar_campos_farmacia(nome_fantasia, cnpj_raw, endereco, responsavel, latitude, longitude)
    if erro:
        flash(erro, "danger")
        return redirect(url_for("farmacias.listar_farmacias"))

    cnpj = _limpar_cnpj(cnpj_raw)
    if not validar_cnpj(cnpj):
        flash("CNPJ inválido.", "danger")
        return redirect(url_for("farmacias.listar_farmacias"))

    cnpj_fmt = f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"

    if Farmacia.query.filter_by(cnpj=cnpj_fmt).first():
        flash(f'CNPJ "{cnpj_fmt}" já está cadastrado no sistema.', "danger")
        return redirect(url_for("farmacias.listar_farmacias"))

    try:
        # Converter coordenadas se fornecidas
        lat_float = float(latitude) if latitude else None
        lon_float = float(longitude) if longitude else None
        
        farmacia = Farmacia(
            nome_fantasia=nome_fantasia,
            razao_social=razao_social or None,
            cnpj=cnpj_fmt,
            endereco=endereco,
            responsavel=responsavel,
            latitude=lat_float,
            longitude=lon_float
        )
        db.session.add(farmacia)
        db.session.commit()
        registrar_log(
            "Nova Farmácia", f'Farmácia "{nome_fantasia}" ({cnpj_fmt}) cadastrada'
        )
        flash(f'Farmácia "{nome_fantasia}" cadastrada com sucesso!', "success")
    except Exception:
        db.session.rollback()
        flash("Erro ao cadastrar farmácia. Tente novamente.", "danger")

    return redirect(url_for("farmacias.listar_farmacias"))


@farmacias_bp.route("/farmacia/<int:farmacia_id>/editar", methods=["POST"])
@login_required
@farmaceutico_required
def editar_farmacia(farmacia_id):
    farmacia = db.session.get(Farmacia, farmacia_id)
    if not farmacia:
        flash("Farmácia não encontrada.", "danger")
        return redirect(url_for("farmacias.listar_farmacias"))

    nome_fantasia = sanitizar_input_string(request.form.get("nome_fantasia", ""), max_length=_MAX_NOME)
    razao_social = sanitizar_input_string(request.form.get("razao_social", ""), max_length=_MAX_NOME)
    cnpj_raw = request.form.get("cnpj", "").strip()[:_MAX_CNPJ_RAW]
    endereco = sanitizar_input_string(request.form.get("endereco", ""), max_length=_MAX_END)
    responsavel = sanitizar_input_string(request.form.get("responsavel", ""), max_length=_MAX_RESP)
    latitude = request.form.get("latitude", "").strip()
    longitude = request.form.get("longitude", "").strip()

    # Detecta padrões suspeitos
    if detectar_padroes_suspeitos(nome_fantasia) or detectar_padroes_suspeitos(endereco) or detectar_padroes_suspeitos(responsavel):
        flash("Entrada contém caracteres não permitidos.", "danger")
        return redirect(url_for("farmacias.listar_farmacias"))

    erro = _validar_campos_farmacia(nome_fantasia, cnpj_raw, endereco, responsavel, latitude, longitude)
    if erro:
        flash(erro, "danger")
        return redirect(url_for("farmacias.listar_farmacias"))

    cnpj = _limpar_cnpj(cnpj_raw)
    if not validar_cnpj(cnpj):
        flash("CNPJ inválido.", "danger")
        return redirect(url_for("farmacias.listar_farmacias"))

    cnpj_fmt = f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"

    existente = Farmacia.query.filter_by(cnpj=cnpj_fmt).first()
    if existente and existente.id != farmacia_id:
        flash(f'CNPJ "{cnpj_fmt}" já pertence a outra farmácia cadastrada.', "danger")
        return redirect(url_for("farmacias.listar_farmacias"))

    try:
        # Converter coordenadas se fornecidas
        lat_float = float(latitude) if latitude else None
        lon_float = float(longitude) if longitude else None
        
        farmacia.nome_fantasia = nome_fantasia
        farmacia.razao_social = razao_social or None
        farmacia.cnpj = cnpj_fmt
        farmacia.endereco = endereco
        farmacia.responsavel = responsavel
        farmacia.latitude = lat_float
        farmacia.longitude = lon_float
        db.session.commit()
        registrar_log("Edição de Farmácia", f'Farmácia "{nome_fantasia}" atualizada')
        flash(f'Farmácia "{nome_fantasia}" atualizada com sucesso!', "success")
    except Exception:
        db.session.rollback()
        flash("Erro ao atualizar farmácia. Tente novamente.", "danger")

    return redirect(url_for("farmacias.listar_farmacias"))


@farmacias_bp.route("/farmacia/<int:farmacia_id>/excluir", methods=["POST"])
@login_required
@admin_required
@audit_critical_action('EXCLUSÃO_FARMÁCIA')
def excluir_farmacia(farmacia_id):
    farmacia = db.session.get(Farmacia, farmacia_id)
    if not farmacia:
        flash("Farmácia não encontrada.", "danger")
        return redirect(url_for("farmacias.listar_farmacias"))

    nome = farmacia.nome_fantasia
    try:
        db.session.delete(farmacia)
        db.session.commit()
        registrar_log("Exclusão de Farmácia", f'Farmácia "{nome}" removida do sistema')
        flash(f'Farmácia "{nome}" removida com sucesso.', "success")
    except Exception:
        db.session.rollback()
        flash("Erro ao remover farmácia. Tente novamente.", "danger")

    return redirect(url_for("farmacias.listar_farmacias"))
