from flask import Blueprint, request, send_file, abort, jsonify, current_app
from flask_login import login_required, current_user
from app.models.receita_anexo import ReceitaAnexo
from app.models.reserva_oferta import ReservaOferta, StatusReserva
from app.database import db
from app.utils.private_storage import get_private_storage_service
from app.utils.log_helper import registrar_log
import os


receita_anexo_bp = Blueprint("receita_anexo", __name__, url_prefix="/receita-anexo")


@receita_anexo_bp.route("/<int:reserva_id>/upload", methods=["POST"])
@login_required
def upload_receita(reserva_id):
    """
    Faz upload de uma receita digitalizada para uma reserva.
    
    Apenas um anexo por reserva. O upload não aprova a reserva.
    """
    reserva = db.session.get(ReservaOferta, reserva_id)
    if not reserva:
        abort(404, "Reserva não encontrada")
    
    # Verifica se a reserva está em status RESERVADA
    if reserva.status != StatusReserva.RESERVADA.value:
        abort(400, f"Upload só permitido para reservas em status RESERVADA. Status atual: {reserva.status}")
    
    # Verifica se já existe anexo para esta reserva
    anexo_existente = ReceitaAnexo.query.filter_by(reserva_id=reserva_id).first()
    if anexo_existente:
        abort(400, "Já existe um anexo de receita para esta reserva")
    
    # Verifica se há arquivo no request
    if 'receita' not in request.files:
        abort(400, "Nenhum arquivo fornecido")
    
    file = request.files['receita']
    
    if file.filename == '':
        abort(400, "Nenhum arquivo selecionado")
    
    # Usa o serviço de armazenamento privado
    storage_service = get_private_storage_service()
    
    # Valida e salva o arquivo
    file_metadata = storage_service.save_file(file, subfolder='receitas')
    
    if not file_metadata:
        is_valid, error_msg = storage_service.validate_file(file)
        abort(400, f"Erro ao salvar arquivo: {error_msg}")
    
    try:
        # Cria registro de anexo
        anexo = ReceitaAnexo(
            reserva_id=reserva_id,
            nome_arquivo_original=file_metadata['nome_arquivo_original'],
            nome_arquivo_interno=file_metadata['nome_arquivo_interno'],
            caminho_arquivo=file_metadata['caminho_arquivo'],
            tamanho_bytes=file_metadata['tamanho_bytes'],
            tipo_mime=file_metadata['tipo_mime'],
            validado=True,
            uploadado_por_id=current_user.id,
            observacoes=request.form.get('observacoes', None)
        )
        db.session.add(anexo)
        db.session.commit()
        
        # Registrar log
        registrar_log(
            "Upload Receita",
            f'Receita digitalizada uploadada para reserva {reserva_id} por usuário {current_user.id}',
        )
        
        return jsonify({
            "success": True,
            "message": "Receita uploadada com sucesso",
            "anexo_id": anexo.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        # Remove arquivo se commit falhou
        storage_service.delete_file(file_metadata['nome_arquivo_interno'], subfolder='receitas')
        current_app.logger.error(f"Erro ao criar registro de anexo: {str(e)}")
        abort(500, "Erro ao salvar anexo de receita")


@receita_anexo_bp.route("/<int:anexo_id>/download", methods=["GET"])
@login_required
def download_receita(anexo_id):
    """
    Faz download de uma receita digitalizada.
    
    Apenas usuários autorizados (vinculados à farmácia de origem) podem baixar.
    """
    anexo = db.session.get(ReceitaAnexo, anexo_id)
    if not anexo:
        abort(404, "Anexo não encontrado")
    
    # Verifica autorização: usuário vinculado à farmácia de origem da reserva
    if not current_user.is_admin and current_user.farmacia_id != anexo.reserva.oferta.farmacia_id:
        abort(403, "Você não tem permissão para acessar este anexo")
    
    # Usa o serviço de armazenamento privado
    storage_service = get_private_storage_service()
    
    file_result = storage_service.get_file(anexo.nome_arquivo_interno, subfolder='receitas')
    
    if not file_result:
        abort(404, "Arquivo não encontrado no armazenamento")
    
    file_path, mime_type = file_result
    
    # Registrar log
    registrar_log(
        "Download Receita",
        f'Receita digitalizada baixada para anexo {anexo_id} por usuário {current_user.id}',
    )
    
    # Envia arquivo como download
    return send_file(
        path_or_file=file_path,
        mimetype=mime_type,
        as_attachment=True,
        download_name=anexo.nome_arquivo_original
    )


@receita_anexo_bp.route("/<int:reserva_id>/status", methods=["GET"])
@login_required
def status_receita(reserva_id):
    """
    Retorna o status da receita para uma reserva.
    
    Verifica se existe anexo e se o medicamento é controlado.
    """
    reserva = db.session.get(ReservaOferta, reserva_id)
    if not reserva:
        abort(404, "Reserva não encontrada")
    
    # Verifica autorização: usuário vinculado à farmácia de origem da reserva
    if not current_user.is_admin and current_user.farmacia_id != reserva.oferta.farmacia_id:
        abort(403, "Você não tem permissão para acessar esta reserva")
    
    # Verifica se medicamento é controlado
    controlado = reserva.oferta.medicamento.controlado
    
    # Verifica se existe anexo
    anexo = ReceitaAnexo.query.filter_by(reserva_id=reserva_id).first()
    
    return jsonify({
        "reserva_id": reserva_id,
        "medicamento_controlado": controlado,
        "receita_anexo_exists": anexo is not None,
        "anexo_id": anexo.id if anexo else None,
        "nome_arquivo_original": anexo.nome_arquivo_original if anexo else None,
        "uploadado_em": anexo.uploadado_em.isoformat() if anexo else None
    })
