"""Rubro: Cubierta de tejas."""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from math import ceil, sqrt

from pydantic import BaseModel, Field, PositiveFloat

from src.datos.loader import (
    cargar_empresa,
    precio_mano_obra,
    precio_material,
)
from src.rubros.base import Partida, ResultadoPresupuesto, registrar


class ParamsCubiertaTejas(BaseModel):
    ancho: PositiveFloat = Field(..., description="Metros")
    largo: PositiveFloat = Field(..., description="Metros")
    tipo_teja: str = Field("ceramica_colonial")
    pendiente_pct: float = Field(30.0, ge=15.0, le=60.0)


CODIGO_TEJA = {
    "ceramica_colonial": "TEJA_CERAMICA_COL",
    "cemento": "TEJA_CEMENTO",
}
TEJAS_POR_M2 = {
    "ceramica_colonial": Decimal("16"),
    "cemento": Decimal("12"),
}


def _q(v: Decimal) -> Decimal:
    return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class CalcCubiertaTejas:
    accion = "cubierta_tejas"
    schema_params = ParamsCubiertaTejas

    @staticmethod
    def calcular(params: ParamsCubiertaTejas, empresa_id: str) -> ResultadoPresupuesto:
        datos = cargar_empresa(empresa_id)
        
        pct = float(params.pendiente_pct) / 100.0
        factor = Decimal(str(sqrt(1 + pct ** 2)))
        ancho = Decimal(str(params.ancho))
        largo = Decimal(str(params.largo))
        m2_real = _q(ancho * largo * factor)

        cod_teja = CODIGO_TEJA.get(params.tipo_teja, "TEJA_CERAMICA_COL")
        tejas_m2 = TEJAS_POR_M2.get(params.tipo_teja, Decimal("16"))
        cant_tejas = Decimal(ceil(m2_real * tejas_m2 * Decimal("1.10")))
        cant_listones = Decimal(ceil(m2_real * Decimal("1.2")))
        cant_cumbreras = Decimal(ceil(largo / Decimal("0.30")))
        p_mo = precio_mano_obra(datos, "CUBIERTA_TEJAS")
        costo_mo = p_mo * m2_real

        partidas = [
            Partida(concepto=f"Teja {params.tipo_teja}", cantidad=cant_tejas, unidad="u", precio_unitario=precio_material(datos, cod_teja), subtotal=cant_tejas * precio_material(datos, cod_teja), categoria="material"),
            Partida(concepto="Listón madera", cantidad=cant_listones, unidad="u", precio_unitario=precio_material(datos, "LISTON_MADERA_2X3"), subtotal=cant_listones * precio_material(datos, "LISTON_MADERA_2X3"), categoria="material"),
            Partida(concepto="Cumbrera cerámica", cantidad=cant_cumbreras, unidad="u", precio_unitario=precio_material(datos, "CUMBRERA_CERAMICA"), subtotal=cant_cumbreras * precio_material(datos, "CUMBRERA_CERAMICA"), categoria="material"),
            Partida(concepto="MO cubierta tejas", cantidad=m2_real, unidad="m2", precio_unitario=p_mo, subtotal=costo_mo, categoria="mano_obra"),
        ]

        total = sum((p.subtotal for p in partidas), Decimal("0"))
        sub_mat = sum((p.subtotal for p in partidas if p.categoria == "material"), Decimal("0"))
        sub_mo = sum((p.subtotal for p in partidas if p.categoria == "mano_obra"), Decimal("0"))

        return ResultadoPresupuesto(
            rubro="cubierta_tejas",
            partidas=partidas,
            subtotal_materiales=sub_mat,
            subtotal_mano_obra=sub_mo,
            total=total,
            metadata={"superficie_m2": float(m2_real), "factor_pendiente": float(factor)},
        )


registrar(CalcCubiertaTejas())
