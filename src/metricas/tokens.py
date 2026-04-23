"""Wrapper sobre persistencia.db para lectura de métricas de tokens."""
from __future__ import annotations

from src.config import settings
from src.persistencia import db


def porcentaje_consumido() -> float:
    usd = db.usd_total_gastado()
    return usd / settings.minimax_budget_usd if settings.minimax_budget_usd > 0 else 0.0


def debe_alertar() -> bool:
    return porcentaje_consumido() >= settings.minimax_alert_threshold


def resumen() -> dict:
    return db.stats_admin() | {
        "budget_usd": settings.minimax_budget_usd,
        "porcentaje": round(porcentaje_consumido() * 100, 2),
    }
