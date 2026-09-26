from flask import Blueprint, render_template
from flask_login import login_required

ajuda_bp = Blueprint("ajuda", __name__)


@ajuda_bp.route("/ajuda")
@login_required
def ajuda():
    """Central de Ajuda e FAQ Operacional - Módulo Aditivo"""
    return render_template("ajuda.html")
