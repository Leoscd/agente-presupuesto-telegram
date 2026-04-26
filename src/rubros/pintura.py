"""Rubro: Pintura interior/exterior."""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from math import ceil
from typing import Literal

from pydantic import BaseModel, Field, PositiveFloat

from src.datos.loader import (
    cargar_empresa,
    precio_mano_obra,
    precio_material,
    rendimiento,
)
from src.rubros.base import Partida, ResultadoPresupuesto, registrar


class ParamsPintura(BaseModel):
    superficie_m2: PositiveFloat
    tipo: Literal["interior", "exterior"]
    manos: int = Field(default=2, ge=1, le=4)
    incluye_fijador: bool = False


def _q(v: Decimal) -> Decimal:
    return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


CODIGO_PINTURA = {
    "interior": "PINTURA_LATEX_INT",
    "exterior": "PINTURA_LATEX_EXT",
}
LITROS_POR_BALDE = Decimal("20")
RENDIMIENTO_L_M2 = Decimal("0.35")  # litros por m2 por mano
RENDIMIENTO_FIJADOR = Decimal("0.15")  # litros por m2


class CalcPintura:
    accion = "pintura"
    schema_params = ParamsPintura

    @staticmethod
    def calcular(params: ParamsPintura, empresa_id: str) -> ResultadoPresupuesto:
        datos = cargar_empresa(empresa_id)

        sup = _q(Decimal(str(params.superficie_m2)))
        cod_pintura = CODIGO_PINTURA[params.tipo]

        # Pintura: litros por m2 por mano / rendimiento
        litros_totales = _q(sup * RENDIMIENTO_L_M2 * Decimal(str(params.manos)))
        # Convertir a baldes
        baldes = Decimal(ceil(litros_totales / LITROS_POR_BALDE))
        pu_pintura = precio_material(datos, cod_pintura)
        subtotal_pintura = _q(pu_pintura * baldes)

        partidas = [
            Partida(
                concepto=f"Pintura látex {params.tipo}",
                cantidad=baldes,
                unidad="u",
                precio_unitario=pu_pintura,
                subtotal=subtotal_pintura,
                categoria="material"
            ),
        ]

        subtotal_materiales = subtotal_pintura

        # Fijador (si aplica)
        if params.incluye_fijador:
            litros_fijador = _q(sup * RENDIMIENTO_FIJADOR)
            baldes_fijador = Decimal(ceil(litros_fijador / LITROS_POR_BALDE))
            pu_fijador = precio_material(datos, "FIJADOR_SELLADOR_4L")
            subtotal_fijador = _q(pu_fijador * baldes_fijador)

            partidas.append(
                Partida(
                    concepto="Fijador sellador",
                    cantidad=baldes_fijador,
                    unidad="u",
                    precio_unitario=pu_fijador,
                    subtotal=subtotal_fijador,
                    categoria="material"
                )
            )
            subtotal_materiales += subtotal_fijador

        # Lija: 1 pliego cada 10m2
        lijadas = sup / Decimal("10")
        # Redondear hacia arriba cada 10m2 = 1 lijada
        lijadas = Decimal(ceil(lijadas))
        pu_lija = precio_material(datos, "LIJA_PAPEL")
        subtotal_lija = _q(pu_lija * lijadas)

        partidas.append(
            Partida(
                concepto="Lija al agua",
                cantidad=lijadas,
                unidad="u",
                precio_unitario=pu_lija,
                subtotal=subtotal_lija,
                categoria="material"
            )
        )
        subtotal_materiales += subtotal_lija

        # MO por m2
        p_mo = precio_mano_obra(datos, "PINTURA")
        costo_mo = _q(p_mo * sup)

        partidas.append(
            Partida(
                concepto="MO pintura",
                cantidad=sup,
                unidad="m2",
                precio_unitario=p_mo,
                subtotal=costo_mo,
                categoria="mano_obra"
            )
        )
        subtotal_mo = costo_mo

        total = subtotal_materiales + subtotal_mo

        return ResultadoPresupuesto(
            rubro="pintura",
            metadata={
                "superficie_m2": params.superficie_m2,
                "tipo": params.tipo,
                "manos": params.manos,
                "incluye_fijador": params.incluye_fijador,
            },
            partidas=partidas,
            subtotal_materiales=subtotal_materiales,
            subtotal_mano_obra=subtotal_mo,
            total=total,
            advertencias=[],
        )


registrar(CalcPintura())