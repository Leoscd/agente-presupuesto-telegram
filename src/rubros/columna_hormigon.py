"""Rubro: Columna de hormigón armado."""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from math import ceil
from typing import Literal

from pydantic import BaseModel, Field, PositiveFloat

from src.datos.loader import (
    cargar_empresa,
    precio_mano_obra,
    precio_material,
)
from src.datos.validador import materiales_faltantes
from src.rubros.base import Partida, ResultadoPresupuesto, registrar


class ParamsColumnaHormigon(BaseModel):
    seccion: Literal["20x20", "25x25", "30x30", "30x40", "40x40"] = "25x25"
    altura_m: PositiveFloat = Field(..., ge=2.0, le=12.0)
    cantidad: int = Field(1, ge=1, le=100)


# Constantes
SECCION_M2 = {
    "20x20": Decimal("0.0400"),
    "25x25": Decimal("0.0625"),
    "30x30": Decimal("0.0900"),
    "30x40": Decimal("0.1200"),
    "40x40": Decimal("0.1600"),
}

DIMS_CM = {
    "20x20": (20, 20),
    "25x25": (25, 25),
    "30x30": (30, 30),
    "30x40": (30, 40),
    "40x40": (40, 40),
}


def _q(v: Decimal) -> Decimal:
    return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class _CalcColumnaHormigon:
    accion = "columna_hormigon"
    schema_params = ParamsColumnaHormigon

    def calcular(self, params: ParamsColumnaHormigon, empresa_id: str) -> ResultadoPresupuesto:
        datos = cargar_empresa(empresa_id)

        faltantes = materiales_faltantes(datos, [
            "CEMENTO_PORTLAND", "ARENA_GRUESA", "PIEDRA_6_12",
            "PLASTIFICANTE_HERCAL", "HIERRO_12", "HIERRO_6",
            "ALAMBRE_ATADO", "TABLON_PINO",
        ])
        if faltantes:
            raise ValueError(
                f"Materiales no disponibles en {empresa_id}: {', '.join(faltantes)}"
            )

        seccion_m2 = SECCION_M2[params.seccion]
        altura = Decimal(str(params.altura_m))
        cantidad = Decimal(str(params.cantidad))

        # Volumen total en m³
        volumen_m3 = _q(seccion_m2 * altura * cantidad)

        # H21: materiales para hormigón
        cemento = Decimal(ceil(volumen_m3 * Decimal("7")))  # bolsas
        arena = _q(volumen_m3 * Decimal("0.45"))  # m3
        piedra = _q(volumen_m3 * Decimal("0.65"))  # m3
        plast = Decimal(max(1, ceil(volumen_m3 / Decimal("5"))))  # bidones

        # Hierro 12mm longitudinal — 4 barras por columna
        # 1 barra = 12m, 11m útiles (descarte 1m)
        cant_barras_12 = Decimal(ceil(params.cantidad * 4 * float(altura) / 11.0))

        # Hierro 6mm estribos — 1 cada 20cm
        estribos_por_col = ceil(float(altura) / 0.20)
        estribos_total = estribos_por_col * params.cantidad

        dim1, dim2 = DIMS_CM[params.seccion]
        perim_estribo = Decimal(str(2 * (dim1 + dim2) / 100 + 0.16))
        ml_hierro6 = Decimal(str(estribos_total)) * perim_estribo
        cant_barras_6 = Decimal(ceil(float(ml_hierro6) / 11.0))

        # Alambre de atar: 0.5 kg por m³
        cant_alambre = _q(volumen_m3 * Decimal("0.5"))

        # Tablones encofrado
        dim1_m = Decimal(str(dim1 / 100))
        dim2_m = Decimal(str(dim2 / 100))
        perim_col = 2 * (dim1_m + dim2_m)
        m2_encofrado = _q(perim_col * altura * cantidad * Decimal("1.10"))
        cant_tablones = Decimal(ceil(float(m2_encofrado) / 0.75))

        # Mano de obra
        p_mo = precio_mano_obra(datos, "COLUMNA_HORMIGON")
        costo_mo = _q(p_mo * volumen_m3)

        # Partidas
        partidas = [
            Partida(
                concepto="Cemento portland",
                cantidad=cemento,
                unidad="u",
                precio_unitario=precio_material(datos, "CEMENTO_PORTLAND"),
                subtotal=_q(cemento * precio_material(datos, "CEMENTO_PORTLAND")),
                categoria="material",
            ),
            Partida(
                concepto="Arena gruesa",
                cantidad=arena,
                unidad="m3",
                precio_unitario=precio_material(datos, "ARENA_GRUESA"),
                subtotal=_q(arena * precio_material(datos, "ARENA_GRUESA")),
                categoria="material",
            ),
            Partida(
                concepto="Piedra partida 6-12mm",
                cantidad=piedra,
                unidad="m3",
                precio_unitario=precio_material(datos, "PIEDRA_6_12"),
                subtotal=_q(piedra * precio_material(datos, "PIEDRA_6_12")),
                categoria="material",
            ),
            Partida(
                concepto="Plastificante Hercal",
                cantidad=plast,
                unidad="u",
                precio_unitario=precio_material(datos, "PLASTIFICANTE_HERCAL"),
                subtotal=_q(plast * precio_material(datos, "PLASTIFICANTE_HERCAL")),
                categoria="material",
            ),
            Partida(
                concepto="Hierro 12mm longitudinal",
                cantidad=cant_barras_12,
                unidad="u",
                precio_unitario=precio_material(datos, "HIERRO_12"),
                subtotal=_q(cant_barras_12 * precio_material(datos, "HIERRO_12")),
                categoria="material",
            ),
            Partida(
                concepto="Hierro 6mm estribos",
                cantidad=cant_barras_6,
                unidad="u",
                precio_unitario=precio_material(datos, "HIERRO_6"),
                subtotal=_q(cant_barras_6 * precio_material(datos, "HIERRO_6")),
                categoria="material",
            ),
            Partida(
                concepto="Alambre de atar",
                cantidad=cant_alambre,
                unidad="kg",
                precio_unitario=precio_material(datos, "ALAMBRE_ATADO"),
                subtotal=_q(cant_alambre * precio_material(datos, "ALAMBRE_ATADO")),
                categoria="material",
            ),
            Partida(
                concepto="Tablon encofrado",
                cantidad=cant_tablones,
                unidad="u",
                precio_unitario=precio_material(datos, "TABLON_PINO"),
                subtotal=_q(cant_tablones * precio_material(datos, "TABLON_PINO")),
                categoria="material",
            ),
            Partida(
                concepto="MO columnas hormigon",
                cantidad=volumen_m3,
                unidad="m3",
                precio_unitario=p_mo,
                subtotal=costo_mo,
                categoria="mano_obra",
            ),
        ]

        total = sum((p.subtotal for p in partidas), Decimal("0"))
        sub_mat = sum((p.subtotal for p in partidas if p.categoria == "material"), Decimal("0"))
        sub_mo = sum((p.subtotal for p in partidas if p.categoria == "mano_obra"), Decimal("0"))

        return ResultadoPresupuesto(
            rubro="columna_hormigon",
            partidas=partidas,
            subtotal_materiales=_q(sub_mat),
            subtotal_mano_obra=_q(sub_mo),
            total=_q(total),
            metadata={
                "volumen_m3": float(volumen_m3),
                "seccion": params.seccion,
                "altura_m": params.altura_m,
                "cantidad": params.cantidad,
            },
            advertencias=[],
        )


registrar(_CalcColumnaHormigon())