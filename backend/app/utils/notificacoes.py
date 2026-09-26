import os
import logging
import threading
from datetime import date, timedelta
from concurrent.futures import ThreadPoolExecutor
from app.models.medicamento import Medicamento

logger = logging.getLogger(__name__)

# Executor global para notificações assíncronas
_notification_executor = ThreadPoolExecutor(max_workers=4)


def medicamentos_estoque_baixo(limite: int = 10):
    """Retorna medicamentos não vencidos com quantidade <= limite."""
    hoje = date.today()
    return (
        Medicamento.query.filter(
            Medicamento.quantidade > 0,
            Medicamento.quantidade <= limite,
            Medicamento.data_validade >= hoje,
        )
        .order_by(Medicamento.quantidade.asc())
        .all()
    )


def medicamentos_vencidos_com_estoque():
    """Retorna medicamentos vencidos que ainda têm estoque (precisam de descarte)."""
    hoje = date.today()
    return (
        Medicamento.query.filter(
            Medicamento.data_validade < hoje,
            Medicamento.quantidade > 0,
        )
        .order_by(Medicamento.data_validade.asc())
        .all()
    )


def contagem_alertas() -> dict:
    """Retorna contagem rápida de alertas críticos para o badge do menu."""
    try:
        hoje = date.today()
        em_30 = hoje + timedelta(days=30)
        vencendo = Medicamento.query.filter(
            Medicamento.data_validade <= em_30,
            Medicamento.data_validade >= hoje,
            Medicamento.quantidade > 0,
        ).count()
        vencidos = Medicamento.query.filter(
            Medicamento.data_validade < hoje,
            Medicamento.quantidade > 0,
        ).count()
        baixo = Medicamento.query.filter(
            Medicamento.quantidade > 0,
            Medicamento.quantidade <= 10,
            Medicamento.data_validade >= hoje,
        ).count()
        return {
            "vencendo": vencendo,
            "vencidos": vencidos,
            "estoque_baixo": baixo,
            "total": vencendo + vencidos + baixo,
        }
    except Exception:
        return {"vencendo": 0, "vencidos": 0, "estoque_baixo": 0, "total": 0}


def enviar_alerta_estoque(titulo: str, mensagem: str) -> dict:
    """Registra um alerta interno sem bloquear a operação IoT."""
    logger.warning("%s: %s", titulo, mensagem)
    return {"ok": True, "mensagem": "Alerta interno registrado.", "enviado": True}


def enviar_email_alertas(destinatario: str, dias: int = 30) -> dict:
    """Envia e-mail com alertas de vencimento e estoque crítico."""
    try:
        from flask_mail import Message
        from main import mail

        meds_vencendo = medicamentos_criticos(dias)
        meds_vencidos = medicamentos_vencidos_com_estoque()
        meds_baixo = medicamentos_estoque_baixo(10)

        if not meds_vencendo and not meds_vencidos and not meds_baixo:
            return {
                "ok": True,
                "mensagem": "Nenhum alerta crítico no momento.",
                "enviado": False,
            }

        hoje = date.today()

        linhas_html = [
            '<div style="font-family:Inter,Arial,sans-serif;max-width:600px;margin:0 auto;background:#1a1a2e;color:#e0e0e0;border-radius:12px;overflow:hidden">',
            '<div style="background:linear-gradient(135deg,#2980b9,#1abc9c);padding:24px 28px">',
            '<h1 style="margin:0;color:#fff;font-size:1.4rem">❤️ RedeVita — Alertas Automáticos</h1>',
            f'<p style="margin:6px 0 0;color:rgba(255,255,255,.8);font-size:.9rem">{hoje.strftime("%d/%m/%Y")}</p>',
            "</div>",
            '<div style="padding:24px 28px">',
        ]

        if meds_vencidos:
            linhas_html += [
                '<h2 style="color:#e74c3c;font-size:1rem;margin:0 0 12px">🔴 Medicamentos Vencidos com Estoque</h2>',
                '<table style="width:100%;border-collapse:collapse;font-size:.85rem;margin-bottom:20px">',
                '<tr style="color:#aaa;font-size:.75rem"><th style="text-align:left;padding:6px 8px;border-bottom:1px solid #333">Medicamento</th>'
                '<th style="text-align:left;padding:6px 8px;border-bottom:1px solid #333">Lote</th>'
                '<th style="text-align:right;padding:6px 8px;border-bottom:1px solid #333">Qtd</th>'
                '<th style="text-align:right;padding:6px 8px;border-bottom:1px solid #333">Vencimento</th></tr>',
            ]
            for m in meds_vencidos:
                linhas_html.append(
                    f'<tr><td style="padding:7px 8px;border-bottom:1px solid #222">{m.nome}</td>'
                    f'<td style="padding:7px 8px;border-bottom:1px solid #222;color:#aaa">{m.lote}</td>'
                    f'<td style="padding:7px 8px;border-bottom:1px solid #222;text-align:right">{m.quantidade}</td>'
                    f'<td style="padding:7px 8px;border-bottom:1px solid #222;text-align:right;color:#e74c3c">{m.data_validade.strftime("%d/%m/%Y")}</td></tr>'
                )
            linhas_html.append("</table>")

        if meds_vencendo:
            linhas_html += [
                f'<h2 style="color:#f39c12;font-size:1rem;margin:0 0 12px">🟡 Vencendo nos Próximos {dias} Dias</h2>',
                '<table style="width:100%;border-collapse:collapse;font-size:.85rem;margin-bottom:20px">',
                '<tr style="color:#aaa;font-size:.75rem"><th style="text-align:left;padding:6px 8px;border-bottom:1px solid #333">Medicamento</th>'
                '<th style="text-align:left;padding:6px 8px;border-bottom:1px solid #333">Lote</th>'
                '<th style="text-align:right;padding:6px 8px;border-bottom:1px solid #333">Qtd</th>'
                '<th style="text-align:right;padding:6px 8px;border-bottom:1px solid #333">Vencimento</th>'
                '<th style="text-align:right;padding:6px 8px;border-bottom:1px solid #333">Dias</th></tr>',
            ]
            for m in meds_vencendo:
                dias_rest = (m.data_validade - hoje).days
                cor = "#e74c3c" if dias_rest <= 7 else "#f39c12"
                linhas_html.append(
                    f'<tr><td style="padding:7px 8px;border-bottom:1px solid #222">{m.nome}</td>'
                    f'<td style="padding:7px 8px;border-bottom:1px solid #222;color:#aaa">{m.lote}</td>'
                    f'<td style="padding:7px 8px;border-bottom:1px solid #222;text-align:right">{m.quantidade}</td>'
                    f'<td style="padding:7px 8px;border-bottom:1px solid #222;text-align:right">{m.data_validade.strftime("%d/%m/%Y")}</td>'
                    f'<td style="padding:7px 8px;border-bottom:1px solid #222;text-align:right;color:{cor};font-weight:700">{dias_rest}d</td></tr>'
                )
            linhas_html.append("</table>")

        if meds_baixo:
            linhas_html += [
                '<h2 style="color:#3498db;font-size:1rem;margin:0 0 12px">🔵 Estoque Crítico (≤ 10 unidades)</h2>',
                '<table style="width:100%;border-collapse:collapse;font-size:.85rem;margin-bottom:20px">',
                '<tr style="color:#aaa;font-size:.75rem"><th style="text-align:left;padding:6px 8px;border-bottom:1px solid #333">Medicamento</th>'
                '<th style="text-align:left;padding:6px 8px;border-bottom:1px solid #333">Lote</th>'
                '<th style="text-align:right;padding:6px 8px;border-bottom:1px solid #333">Qtd</th></tr>',
            ]
            for m in meds_baixo:
                cor = "#e74c3c" if m.quantidade <= 3 else "#3498db"
                linhas_html.append(
                    f'<tr><td style="padding:7px 8px;border-bottom:1px solid #222">{m.nome}</td>'
                    f'<td style="padding:7px 8px;border-bottom:1px solid #222;color:#aaa">{m.lote}</td>'
                    f'<td style="padding:7px 8px;border-bottom:1px solid #222;text-align:right;color:{cor};font-weight:700">{m.quantidade}</td></tr>'
                )
            linhas_html.append("</table>")

        linhas_html += [
            '<p style="color:#888;font-size:.78rem;margin-top:20px;border-top:1px solid #333;padding-top:16px">',
            'Este alerta foi gerado automaticamente pelo <strong style="color:#3498db">RedeVita</strong>. ',
            "Acesse o sistema para tomar as ações necessárias.",
            "</p></div></div>",
        ]

        total = len(meds_vencidos) + len(meds_vencendo) + len(meds_baixo)
        msg = Message(
            subject=f'[RedeVita] ⚠️ {total} alerta(s) crítico(s) — {hoje.strftime("%d/%m/%Y")}',
            recipients=[destinatario],
            html="".join(linhas_html),
        )
        mail.send(msg)
        logger.info(
            "E-mail de alertas enviado para %s (%d alertas)", destinatario, total
        )
        return {
            "ok": True,
            "mensagem": f"E-mail enviado com {total} alerta(s).",
            "enviado": True,
        }

    except Exception as e:
        logger.error("Erro ao enviar e-mail de alertas: %s", e)
        return {
            "ok": False,
            "mensagem": f"Erro ao enviar e-mail: {e}",
            "enviado": False,
        }


def enviar_email_alertas_async(destinatario: str, dias: int = 30) -> None:
    """
    Envia e-mail de alertas de forma assíncrona.
    Não bloqueia a rota HTTP.
    """
    def _send():
        try:
            enviar_email_alertas(destinatario, dias)
        except Exception as e:
            logger.error("Erro no envio assíncrono de alertas: %s", e)
    
    _notification_executor.submit(_send)


def _get_twilio_client():
    from twilio.rest import Client

    sid = os.environ.get("TWILIO_ACCOUNT_SID", "").strip()
    token = os.environ.get("TWILIO_AUTH_TOKEN", "").strip()
    if not sid or not token:
        raise RuntimeError(
            "Credenciais Twilio não configuradas (TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN)."
        )
    return Client(sid, token)


def _numero_from() -> str:
    n = os.environ.get("TWILIO_FROM_NUMBER", "").strip()
    if not n:
        raise RuntimeError("TWILIO_FROM_NUMBER não configurado.")
    return n


def medicamentos_criticos(dias: int = 60):
    hoje = date.today()
    limite = hoje + timedelta(days=dias)
    return (
        Medicamento.query.filter(Medicamento.data_validade <= limite)
        .order_by(Medicamento.data_validade.asc())
        .all()
    )


def _montar_mensagem(meds, dias: int) -> str:
    hoje = date.today()
    linhas = [f'*RedeVita — Alerta de Validade* ({hoje.strftime("%d/%m/%Y")})\n']
    for m in meds:
        restantes = (m.data_validade - hoje).days
        if restantes < 0:
            status = "VENCIDO"
        elif restantes == 0:
            status = "Vence HOJE"
        else:
            status = f"Vence em {restantes} dia(s)"
        linhas.append(f"• {m.nome} (Lote {m.lote}) — {status} — {m.quantidade} un.")
    linhas.append(f"\nTotal: {len(meds)} medicamento(s) nos próximos {dias} dias.")
    return "\n".join(linhas)


def enviar_sms(telefone: str, dias: int = 60) -> dict:
    meds = medicamentos_criticos(dias)
    if not meds:
        return {
            "ok": True,
            "mensagem": "Nenhum medicamento crítico encontrado.",
            "enviado": False,
        }
    mensagem = _montar_mensagem(meds, dias)
    try:
        client = _get_twilio_client()
        msg = client.messages.create(body=mensagem, from_=_numero_from(), to=telefone)
        logger.info("SMS enviado para %s — SID %s", telefone, msg.sid)
        return {
            "ok": True,
            "mensagem": f"SMS enviado ({len(meds)} med(s)).",
            "sid": msg.sid,
            "enviado": True,
        }
    except RuntimeError as e:
        return {"ok": False, "mensagem": str(e), "enviado": False}
    except Exception as e:
        logger.error("Erro ao enviar SMS: %s", e)
        return {"ok": False, "mensagem": f"Erro ao enviar SMS: {e}", "enviado": False}


def enviar_whatsapp(telefone: str, dias: int = 60) -> dict:
    meds = medicamentos_criticos(dias)
    if not meds:
        return {
            "ok": True,
            "mensagem": "Nenhum medicamento crítico encontrado.",
            "enviado": False,
        }
    mensagem = _montar_mensagem(meds, dias)
    try:
        client = _get_twilio_client()
        numero_from = _numero_from()
        from_wa = (
            f"whatsapp:{numero_from}"
            if not numero_from.startswith("whatsapp:")
            else numero_from
        )
        to_wa = (
            f"whatsapp:{telefone}" if not telefone.startswith("whatsapp:") else telefone
        )
        msg = client.messages.create(body=mensagem, from_=from_wa, to=to_wa)
        logger.info("WhatsApp enviado para %s — SID %s", telefone, msg.sid)
        return {
            "ok": True,
            "mensagem": f"WhatsApp enviado ({len(meds)} med(s)).",
            "sid": msg.sid,
            "enviado": True,
        }
    except RuntimeError as e:
        return {"ok": False, "mensagem": str(e), "enviado": False}
    except Exception as e:
        logger.error("Erro ao enviar WhatsApp: %s", e)
        return {
            "ok": False,
            "mensagem": f"Erro ao enviar WhatsApp: {e}",
            "enviado": False,
        }


def enviar_notificacao_dispensacao(telefone: str, paciente_nome: str, medicamento_nome: str, farmacia_nome: str = "") -> dict:
    """
    Envia notificação WhatsApp/SMS quando uma prescrição é dispensada/liberada.
    
    Args:
        telefone: Número de telefone do paciente (formato: +5511999999999)
        paciente_nome: Nome do paciente
        medicamento_nome: Nome do medicamento dispensado
        farmacia_nome: Nome da farmácia (opcional)
    
    Returns:
        dict: Resultado do envio
    """
    mensagem = f"""*RedeVita — Medicamento Liberado* ✅

Olá, {paciente_nome}!

Seu medicamento foi liberado e está pronto para retirada:
💊 {medicamento_nome}"""
    
    if farmacia_nome:
        mensagem += f"\n🏥 Local: {farmacia_nome}"
    
    mensagem += "\n\nApresente este comprovante no local de retirada."
    
    # Tenta WhatsApp primeiro, fallback para SMS
    try:
        client = _get_twilio_client()
        numero_from = _numero_from()
        
        # WhatsApp
        from_wa = f"whatsapp:{numero_from}" if not numero_from.startswith("whatsapp:") else numero_from
        to_wa = f"whatsapp:{telefone}" if not telefone.startswith("whatsapp:") else telefone
        
        try:
            msg = client.messages.create(body=mensagem, from_=from_wa, to=to_wa)
            logger.info("Notificação WhatsApp enviada para %s — SID %s", telefone, msg.sid)
            return {
                "ok": True,
                "mensagem": "Notificação WhatsApp enviada com sucesso.",
                "sid": msg.sid,
                "canal": "whatsapp",
                "enviado": True,
            }
        except Exception as wa_error:
            logger.warning("Falha ao enviar WhatsApp, tentando SMS: %s", wa_error)
            # Fallback para SMS
            msg = client.messages.create(body=mensagem, from_=numero_from, to=telefone)
            logger.info("Notificação SMS enviada para %s — SID %s", telefone, msg.sid)
            return {
                "ok": True,
                "mensagem": "Notificação SMS enviada com sucesso.",
                "sid": msg.sid,
                "canal": "sms",
                "enviado": True,
            }
    except RuntimeError as e:
        return {"ok": False, "mensagem": str(e), "enviado": False}
    except Exception as e:
        logger.error("Erro ao enviar notificação de dispensação: %s", e)
        return {
            "ok": False,
            "mensagem": f"Erro ao enviar notificação: {e}",
            "enviado": False,
        }
