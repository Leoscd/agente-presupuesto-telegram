"""Rubro: Revoque fino (terminación antes de pintar)."""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from math import ceil

from pydantic import BaseModel, Field, PositiveFloat

from src.datos.loader import cargar_empresa, precio_mano_obra, precio_material
from src.datos.validador import materiales_faltantes
from src.rubros.base import Partida, ResultadoPresupuesto, registrar


class ParamsRevoqueFino(BaseModel):
    superficie_m2: PositiveFloat = Field(..., description="Metros cuadrados")
    espesor_cm: float = Field(0.5, ge=0.3, le=1.0)


def _q(v: Decimal) -> Decimal:
    return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class CalcRevoqueFino:
    accion = "revoque_fino"
    schema_params = ParamsRevoqueFino

    @staticmethod
    def calcular(params: ParamsRevoqueFino, empresa_id: str) -> ResultadoPresupuesto:
        datos = cargar_empresa(empresa_id)
        sup = Decimal(str(params.superficie_m2))

        # Yeso: 1 bolsa de 40kg cubre ~8m2
        # ceil(superficie_m2 / 8) bolsas
        cant_yeso = ceil(sup / Decimal("8"))

        # Mano de obra
        costo_mo = precio_mano_obra(datos, "REVOQUE_FINO") * sup

        partidas = []

        # Yeso bolsa 40kg
        partidas.append(Partida(
            concepto="Yeso bolsa 40kg",
            cantidad=cant_yeso,
            unidad="u",
            precio_unitario=precio_material(datos, "YESO_BOLSA"),
            subtotal=cant_yeso * precio_material(datos, "YESO_BOLSA"),
            categoria="material"
        ))

        # Mano de obra
        partidas.append(Partida(
            concepto="MO revoque fino",
            cantidad=float(sup),
            unidad="m2",
            precio_unitario=costo_mo / sup,
            subtotal=costo_mo,
            categoria="mano_obra"
        ))

        materiales_faltantes(partidas, datos)

        total = sum((p.subtotal for p in partidas), Decimal("0"))
        sub_mat = sum((p.subtotal for p in partidas if p.categoria == "material"), Decimal("0"))
        sub_mo = sum((p.subtotal for p in partidas if p.categoria == "mano_obra"), Decimal("0"))

        return ResultadoPresupuesto(
            rubro="revoque_fino",
            partidas=partidas,
            subtotal_materiales=sub_mat,
            subtotal_mano_obra=sub_mo,
            total=total,
            metadata={"superficie_m2": params.superficie_m2},
        )


registrar(CalcRevoqueFino())