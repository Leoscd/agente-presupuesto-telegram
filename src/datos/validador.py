from __future__ import annotations

from src.datos.loader import DatosEmpresa


def materiales_faltantes(datos: DatosEmpresa, codigos: list[str]) -> list[str]:
    """Devuelve los códigos que NO están en materiales_disponibles.json."""
    disp = set(datos.materiales_disponibles)
    return [c for c in codigos if c not in disp]
