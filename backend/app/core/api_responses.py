from flask import jsonify


def resposta_ok(dados=None, mensagem=None, status=200):
    corpo = {"sucesso": True, "success": True}
    if mensagem:
        corpo["mensagem"] = mensagem
    if dados is not None:
        corpo["dados"] = dados
        corpo["data"] = dados
    return jsonify(corpo), status


def resposta_erro(mensagem, status=400, detalhes=None):
    corpo = {"sucesso": False, "success": False, "erro": mensagem}
    if isinstance(mensagem, dict):
        corpo["message"] = mensagem.get("mensagem", str(mensagem))
    else:
        corpo["message"] = mensagem
    if detalhes:
        corpo["detalhes"] = detalhes
    return jsonify(corpo), status
