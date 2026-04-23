"""Registry de calculadoras. Importar este paquete registra todos los rubros."""
from __future__ import annotations

from src.rubros.base import REGISTRY, Calculadora, Partida, ResultadoPresupuesto, registrar

# Importaciones con side-effect: cada módulo se auto-registra en REGISTRY.
from src.rubros import techo_chapa  # noqa: F401,E402

__all__ = ["REGISTRY", "Calculadora", "Partida", "ResultadoPresupuesto", "registrar"]
