"""Registry de calculadoras. Importar este paquete registra todos los rubros."""
from __future__ import annotations

from src.rubros.base import REGISTRY, Calculadora, Partida, ResultadoPresupuesto, registrar

# Importaciones con side-effect: cada módulo se auto-registra en REGISTRY.
from src.rubros import (  # noqa: F401
    techo_chapa,
    cubierta_tejas,
    mamposteria,
    losa,
    contrapiso,
    revoque_grueso,
    revestimiento_banio,
    instalacion_electrica,
    instalacion_sanitaria,
    revoque_fino,
    piso_ceramico,
    fundacion,
    escalera_hormigon,
    membrana_impermeabilizante,
    estructura_metalica,
    pintura,
    cielorraso_durlock,
    columna_hormigon,
    viga_encadenado,
)

__all__ = ["REGISTRY", "Calculadora", "Partida", "ResultadoPresupuesto", "registrar"]
