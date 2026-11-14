from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models.doacao import Doacao
from app.models.doacao_etapa import DoacaoEtapa, TipoEtapa, OrigemEvento
from app.database import db
from app.core.decorators import admin_required, operador_required, equipe_clinica_required
from datetime import datetime

recibo_doacao_bp = Blueprint("recibo_doacao", __name__)


@recibo_doacao_bp.route("/doacoes/<int:doacao_id>/recibo", methods=["GET"])
@login_required
@operador_required
def recibo(doacao_id):
    """Exibe o recibo de etapas de uma doação."""
    doacao = Doacao.query.get_or_404(doacao_id)

    # Verificação de autorização: Admin pode ver tudo, operador só pode ver suas próprias doações
    if current_user.cargo != "Admin" and doacao.usuario_id != current_user.id:
        flash("Você não tem permissão para visualizar este recibo.", "danger")
        return redirect(url_for("donation.nova_doacao"))

    # Busca etapas ordenadas cronologicamente
    etapas = DoacaoEtapa.query.filter_by(doacao_id=doacao_id).order_by(DoacaoEtapa.data_hora.asc()).all()

    return render_template(
        "recibo_doacao.html",
        doacao=doacao,
        etapas=etapas,
        TipoEtapa=TipoEtapa,
        OrigemEvento=OrigemEvento
    )


@recibo_doacao_bp.route("/api/doacoes/<int:doacao_id>/etapas", methods=["GET"])
@login_required
@operador_required
def api_etapas(doacao_id):
    """API para buscar etapas de uma doação (JSON)."""
    doacao = Doacao.query.get_or_404(doacao_id)

    # Verificação de autorização
    if current_user.cargo != "Admin" and doacao.usuario_id != current_user.id:
        return jsonify({"erro": "Não autorizado"}), 403

    etapas = DoacaoEtapa.query.filter_by(doacao_id=doacao_id).order_by(DoacaoEtapa.data_hora.asc()).all()

    return jsonify({
        "doacao_id": doacao_id,
        "etapas": [etapa.to_dict() for etapa in etapas]
    })
