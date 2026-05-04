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
)
from src.datos.validador import materiales_faltantes
from src.rubros.base import Partida, ResultadoPresupuesto, registrar


class ParamsPintura(BaseModel):
    superficie_m2: PositiveFloat
    tipo: Literal["latex_interior", "latex_exterior", "esmalte_sintetico"] = "latex_interior"
    manos: int = Field(default=2, ge=1, le=4)
    incluye_fijador: bool = True


def _q(v: Decimal) -> Decimal:
    return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


CODIGO_PINTURA = {
    "latex_interior":    "PINTURA_LATEX_INT",
    "latex_exterior":    "PINTURA_LATEX_EXT",
    "esmalte_sintetico": "PINTURA_ESMALTE",
}
LITROS_POR_BALDE = {
    "latex_interior":    Decimal("20"),
    "latex_exterior":    Decimal("20"),
    "esmalte_sintetico": Decimal("4"),
}
RENDIMIENTO_L_M2 = Decimal("12")         # m2 por litro por mano
RENDIMIENTO_FIJADOR_L_M2 = Decimal("15") # m2 por litro de fijador
LITROS_BALDE_FIJADOR = Decimal("4")


class _CalcPintura:
    accion = "pintura"
    schema_params = ParamsPintura

    def calcular(self, params: ParamsPintura, empresa_id: str) -> ResultadoPresupuesto:
        assert isinstance(params, ParamsPintura)
        datos = cargar_empresa(empresa_id)

        cod_pintura = CODIGO_PINTURA[params.tipo]
        codigos_usados = [cod_pintura, "LIJA_PAPEL"]
        if params.incluye_fijador:
            codigos_usados.append("FIJADOR_SELLADOR_4L")

        faltantes = materiales_faltantes(datos, codigos_usados)
        if faltantes:
            raise ValueError(
                f"Materiales no disponibles en {empresa_id}: {', '.join(faltantes)}"
            )

        sup = Decimal(str(params.superficie_m2))

        # Pintura: m2 / rendimiento (m2/L) * manos = litros necesarios
        litros_pintura = sup * Decimal(str(params.manos)) / RENDIMIENTO_L_M2
        cant_baldes_pin = Decimal(ceil(float(litros_pintura) / float(LITROS_POR_BALDE[params.tipo])))
        pu_pintura = precio_material(datos, cod_pintura)
        subtotal_pintura = _q(pu_pintura * cant_baldes_pin)

        partidas = [
            Partida(
                concepto=f"Pintura {params.tipo} balde",
                cantidad=cant_baldes_pin,
                unidad="u",
                precio_unitario=pu_pintura,
                subtotal=subtotal_pintura,
                categoria="material",
            ),
        ]

        subtotal_materiales = subtotal_pintura

        # Fijador (si aplica)
        if params.incluye_fijador:
            litros_fijador = sup / RENDIMIENTO_FIJADOR_L_M2
            cant_baldes_fijador = Decimal(ceil(float(litros_fijador) / float(LITROS_BALDE_FIJADOR)))
            pu_fijador = precio_material(datos, "FIJADOR_SELLADOR_4L")
            subtotal_fijador = _q(pu_fijador * cant_baldes_fijador)

            partidas.append(
                Partida(
                    concepto="Fijador sellador balde 4L",
                    cantidad=cant_baldes_fijador,
                    unidad="u",
                    precio_unitario=pu_fijador,
                    subtotal=subtotal_fijador,
                    categoria="material",
                )
            )
            subtotal_materiales += subtotal_fijador

        # Lija: 1 pliego cada 10m2
        cant_lija = Decimal(ceil(float(sup) / 10.0))
        pu_lija = precio_material(datos, "LIJA_PAPEL")
        subtotal_lija = _q(pu_lija * cant_lija)

        partidas.append(
            Partida(
                concepto="Lija pliego N120",
                cantidad=cant_lija,
                unidad="u",
                precio_unitario=pu_lija,
                subtotal=subtotal_lija,
                categoria="material",
            )
        )
        subtotal_materiales += subtotal_lija

        # MO por m2
        p_mo = precio_mano_obra(datos, "PINTURA")
        costo_mo = _q(p_mo * sup)

        partidas.append(
            Partida(
                concepto="MO pintura",
                cantidad=_q(sup),
                unidad="m2",
                precio_unitario=p_mo,
                subtotal=costo_mo,
                categoria="mano_obra",
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
            subtotal_materiales=_q(subtotal_materiales),
            subtotal_mano_obra=_q(subtotal_mo),
            total=_q(total),
            advertencias=[],
        )


registrar(_CalcPintura())