"""Handlers de Telegram."""
from __future__ import annotations

import json
import logging
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

from src.bot import auth, formatter
from src.config import settings
from src.datos.loader import cargar_empresa, actualizar_precio_material, actualizar_precio_mano_obra, listar_materiales_con_descripcion, listar_mo_con_descripcion
from src.metricas import tokens
from src.orquestador import minimax_client, router
from src.persistencia import db
from src.pdf import generador

log = logging.getLogger(__name__)

TMP_OUT = settings.db_path.parent.parent / "out"
CONFIANZA_MIN = 0.70
OUTLIER_FACTOR = 1.30


async def cmd_start(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if user is None or update.message is None:
        return
    empresa_id = auth.resolver_empresa(user.id)
    datos = cargar_empresa(empresa_id)
    await update.message.reply_text(
        f"Hola, {user.first_name}. Bot de presupuestos conectado a *{datos.config.nombre}*.\n\n"
        "Escribí un pedido como:\n"
        "`techo chapa galvanizada 7x10 con perfil C100`\n\n"
        "Comandos: /empresa /tokens /help",
        parse_mode=ParseMode.MARKDOWN,
    )


async def cmd_empresa(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user is None or update.message is None:
        return
    empresa_id = auth.resolver_empresa(update.effective_user.id)
    datos = cargar_empresa(empresa_id)
    await update.message.reply_text(
        f"Empresa: {datos.config.nombre} ({empresa_id})\n"
        f"Moneda: {datos.config.moneda}\n"
        f"Materiales disponibles: {len(datos.materiales_disponibles)}\n"
        f"Tarifas de mano de obra: {len(datos.precios_mano_obra)}"
    )


async def cmd_tokens(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user is None or update.message is None:
        return
    if not auth.es_admin(update.effective_user.id):
        await update.message.reply_text("Solo admin.")
        return
    r = tokens.resumen()
    await update.message.reply_text(
        f"Presupuestos: {r['presupuestos']}\n"
        f"Llamadas MiniMax: {r['calls_minimax']}\n"
        f"Tokens in/out: {r['tokens_input']} / {r['tokens_output']}\n"
        f"USD gastado: ${r['usd_gastado']:.4f} / ${r['budget_usd']:.2f} ({r['porcentaje']}%)\n"
        f"USD restante: ${r['usd_restante']:.4f}"
    )


async def on_mensaje(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user is None or update.message is None or update.message.text is None:
        return

    user_id = update.effective_user.id
    texto = update.message.text

    try:
        empresa_id = auth.resolver_empresa(user_id)
    except PermissionError as e:
        await update.message.reply_text(str(e))
        return

    datos = cargar_empresa(empresa_id)

    # 1) NLU con MiniMax
    await update.message.chat.send_action(action="typing")
    try:
        resp = await minimax_client.parsear(texto, datos.materiales_disponibles)
    except Exception as e:  # noqa: BLE001
        log.exception("Error MiniMax")
        await update.message.reply_text(f"Error consultando el orquestador: {e}")
        return

    log.info("NLU: %s (conf=%.2f, tokens=%d/%d, $%.5f)",
             resp.accion, resp.confianza, resp.tokens_input, resp.tokens_output, resp.usd_estimado)

    # 2) Aclaración o confianza baja
    if resp.accion == "aclaracion":
        pregunta = resp.parametros.get("pregunta", "¿Podés dar más detalles?")
        await update.message.reply_text(f"❓ {pregunta}")
        return

    if resp.confianza < CONFIANZA_MIN:
        await update.message.reply_text(
            f"No estoy seguro de haber entendido (confianza {resp.confianza:.0%}). "
            f"Interpreté: {resp.accion} {resp.parametros}. Reformulá, por favor."
        )
        return

    # 3) Cálculo
    try:
        resultado = router.despachar(resp.accion, resp.parametros, empresa_id)
    except router.AccionDesconocida as e:
        await update.message.reply_text(f"No tengo una calculadora para eso todavía. {e}")
        return
    except ValueError as e:
        await update.message.reply_text(f"No pude calcular: {e}")
        return

    # 4) Outlier check
    mediana = db.mediana_total(empresa_id, resultado.rubro)
    if mediana and float(resultado.total) > mediana * OUTLIER_FACTOR:
        resultado.advertencias.append(
            f"Total {float(resultado.total)/mediana:.0%} por encima de la mediana "
            f"({mediana:.0f}). Revisá precios."
        )
        if settings.admin_telegram_chat_id:
            await _ctx.bot.send_message(
                settings.admin_telegram_chat_id,
                f"⚠️ Outlier en {empresa_id}: {resultado.rubro} = {resultado.total} "
                f"(mediana {mediana:.0f})",
            )

    # 5) Persistir
    pid, id_corto = db.guardar_presupuesto(
        empresa_id=empresa_id,
        telegram_user_id=user_id,
        input_texto=texto,
        minimax_json=resp.raw,
        minimax_confianza=resp.confianza,
        resultado=resultado,
        tokens_input=resp.tokens_input,
        tokens_output=resp.tokens_output,
        usd_estimado=resp.usd_estimado,
        latencia_ms=resp.latencia_ms,
    )

    # 6) Responder
    texto_ok = formatter.formatear_presupuesto(resultado, id_corto)
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📄 Generar PDF", callback_data=f"pdf:{pid}")],
        [
            InlineKeyboardButton("✅ Preciso", callback_data=f"fb_ok:{pid}"),
            InlineKeyboardButton("❌ Corregir", callback_data=f"fb_bad:{pid}"),
        ],
    ])
    await update.message.reply_text(texto_ok, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb)

    # 7) Alerta de tokens
    if tokens.debe_alertar() and settings.admin_telegram_chat_id:
        r = tokens.resumen()
        await _ctx.bot.send_message(
            settings.admin_telegram_chat_id,
            f"⚠️ Consumo MiniMax al {r['porcentaje']}% (${r['usd_gastado']}/${r['budget_usd']})",
        )


async def on_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    if q is None or q.data is None:
        return
    await q.answer()
    accion, _, pid_s = q.data.partition(":")
    pid = int(pid_s) if pid_s.isdigit() else 0

    if accion == "pdf" and pid:
        await _enviar_pdf(update, ctx, pid)
    elif accion == "fb_ok" and pid:
        db.guardar_feedback(pid, preciso=True)
        await q.edit_message_reply_markup(reply_markup=None)
        if q.message:
            await q.message.reply_text("✅ Gracias por el feedback.")
    elif accion == "fb_bad" and pid:
        db.guardar_feedback(pid, preciso=False)
        if q.message:
            await q.message.reply_text(
                "Enviame el total real que calculaste (solo un número) o escribí una nota con /nota <id> <texto>."
            )


async def _enviar_pdf(update: Update, ctx: ContextTypes.DEFAULT_TYPE, pid: int) -> None:
    from src.persistencia.db import cursor
    from src.rubros.base import ResultadoPresupuesto as _R

    with cursor() as c:
        row = c.execute(
            "SELECT empresa_id, resultado_json FROM presupuestos WHERE id=?", (pid,)
        ).fetchone()
    if not row:
        return
    resultado = _R.model_validate_json(row["resultado_json"])
    datos = cargar_empresa(row["empresa_id"])

    TMP_OUT.mkdir(parents=True, exist_ok=True)
    pdf_path = generador.generar_pdf(resultado, datos, TMP_OUT)

    if update.effective_chat:
        await ctx.bot.send_document(
            chat_id=update.effective_chat.id,
            document=pdf_path.open("rb"),
            filename=pdf_path.name,
        )
    _actualizar_pdf_path(pid, pdf_path)


def _actualizar_pdf_path(pid: int, path: Path) -> None:
    from src.persistencia.db import cursor
    with cursor() as c:
        c.execute("UPDATE presupuestos SET pdf_path=? WHERE id=?", (str(path), pid))


def registrar(app) -> None:  # type: ignore[no-untyped-def]
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_start))
    app.add_handler(CommandHandler("empresa", cmd_empresa))
    app.add_handler(CommandHandler("tokens", cmd_tokens))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_mensaje))
