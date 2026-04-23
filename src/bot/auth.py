"""Mapeo Telegram user_id → empresa_id, con fallback para admin en dev."""
from __future__ import annotations

from src.config import settings
from src.persistencia import db


DEFAULT_EMPRESA_DEV = "estudio_ramos"


def resolver_empresa(telegram_user_id: int) -> str:
    empresa = db.empresa_de(telegram_user_id)
    if empresa:
        return empresa
    if settings.env == "dev":
        # En dev auto-vinculamos a estudio_ramos para acelerar pruebas
        db.vincular_usuario(telegram_user_id, DEFAULT_EMPRESA_DEV, es_admin=True)
        return DEFAULT_EMPRESA_DEV
    raise PermissionError(
        f"Usuario {telegram_user_id} no está vinculado a ninguna empresa. "
        "Contactá al administrador."
    )


def es_admin(telegram_user_id: int) -> bool:
    if settings.admin_telegram_chat_id and telegram_user_id == settings.admin_telegram_chat_id:
        return True
    from src.persistencia.db import cursor
    with cursor() as c:
        row = c.execute(
            "SELECT es_admin FROM usuarios WHERE telegram_user_id=?", (telegram_user_id,)
        ).fetchone()
    return bool(row and row["es_admin"])
