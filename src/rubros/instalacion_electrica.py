"""Rubro: Instalación eléctrica."""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from math import ceil

from pydantic import BaseModel, Field, PositiveFloat

from src.datos.loader import cargar_empresa, precio_mano_obra, precio_material
from src.datos.validador import materiales_faltantes
from src.rubros.base import Partida, ResultadoPresupuesto, registrar


class ParamsInstalacionElectrica(BaseModel):
    superficie_m2: PositiveFloat = Field(..., description="Superficie del local/vivienda")
    tipo: str = Field("basica", description="basica = 1 circuito, completa = 2+")
    cantidad_bocas: int = Field(0, ge=0, description="Si 0, calcular por m2")
    incluye_tablero: bool = Field(True)


def _q(v: Decimal) -> Decimal:
    return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class CalcInstalacionElectrica:
    accion = "instalacion_electrica"
    schema_params = ParamsInstalacionElectrica

    @staticmethod
    def calcular(params: ParamsInstalacionElectrica, empresa_id: str) -> ResultadoPresupuesto:
        datos = cargar_empresa(empresa_id)
        sup = Decimal(str(params.superficie_m2))

        # Bocas: si 0, calcular por m2 (~1 cada 4m2)
        bocas = params.cantidad_bocas
        if bocas == 0:
            bocas = int(ceil(sup / Decimal("4")))

        # Cable: bocas * 3.5 ml
        cable_ml = bocas * Decimal("3.5")
        
        # Cao: cable * 1.1
        caño_ml = cable_ml * Decimal("1.1")

        # Tablero
        cant_tablero = 1 if params.incluye_tablero else 0

        # Llaves y tomacorrientes: bocas unidades
        cant_tomas = bocas

        # Materiales
        partidas = []

        # Cable 2x2.5
        partidas.append(Partida(
            concepto="Cable IRAM 2x2.5mm",
            cantidad=cable_ml,
            unidad="ml",
            precio_unitario=precio_material(datos, "CABLE_IRAM_2X2_5"),
            subtotal=cable_ml * precio_material(datos, "CABLE_IRAM_2X2_5"),
            categoria="material"
        ))

        # Cao corrugado
        partidas.append(Partida(
            concepto="Cao corrugado 20mm",
            cantidad=caño_ml,
            unidad="ml",
            precio_unitario=precio_material(datos, "CANO_CORRUGADO_20"),
            subtotal=caño_ml * precio_material(datos, "CANO_CORRUGADO_20"),
            categoria="material"
        ))

        # Tablero
        if cant_tablero:
            partidas.append(Partida(
                concepto="Tablero monofasico 12 modulos",
                cantidad=1,
                unidad="u",
                precio_unitario=precio_material(datos, "TABLERO_MONOF_12"),
                subtotal=precio_material(datos, "TABLERO_MONOF_12"),
                categoria="material"
            ))

        # Tomas
        partidas.append(Partida(
            concepto="Tomacorriente 2P+T",
            cantidad=cant_tomas,
            unidad="u",
            precio_unitario=precio_material(datos, "TOMACORRIENTE_2P"),
            subtotal=cant_tomas * precio_material(datos, "TOMACORRIENTE_2P"),
            categoria="material"
        ))

        # Mano de obra
        costo_mo = precio_mano_obra(datos, "INSTALACION_ELECTRICA") * sup
        partidas.append(Partida(
            concepto="MO instalacion electrica",
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
            rubro="instalacion_electrica",
            partidas=partidas,
            subtotal_materiales=sub_mat,
            subtotal_mano_obra=sub_mo,
            total=total,
            metadata={"superficie_m2": float(sup), "cantidad_bocas": bocas},
        )


registrar(CalcInstalacionElectrica())