"""Rubro: Revestimiento de baño/cocina."""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from math import ceil

from pydantic import BaseModel, Field, model_validator

from src.datos.loader import (
    DatosEmpresa,
    cargar_empresa,
    precio_mano_obra,
    precio_material,
    rendimiento,
)
from src.datos.validador import materiales_faltantes
from src.rubros.base import Partida, ResultadoPresupuesto, registrar


class ParamsRevestimientoBanio(BaseModel):
    superficie_piso_m2: float = Field(0.0, ge=0.0)
    superficie_pared_m2: float = Field(0.0, ge=0.0)
    material_piso: str = Field("porcelanato_60x60")
    material_pared: str = Field("ceramico_pared_25x35")
    incluye_alzada_cocina: bool = Field(False)
    superficie_alzada_m2: float = Field(0.0, ge=0.0)

    @model_validator(mode="after")
    def al_menos_una_superficie(self):
        if self.superficie_piso_m2 == 0 and self.superficie_pared_m2 == 0:
            raise ValueError("Debe especificar superficie de piso y/o paredes")
        return self


CODIGO_MATERIAL = {
    "porcelanato_60x60": "PORCELANATO_60X60",
    "porcelanato_60x60_premium": "PORCELANATO_60X60_PREMIUM",
    "ceramico_pared_25x35": "CERAMICO_PARED_25X35",
    "ceramico_30x30": "CERAMICO_30X30",
    "ceramico_45x45": "CERAMICO_45X45",
}
CODIGO_ADHESIVO = {
    "porcelanato_60x60": "ADHESIVO_PORCELANATO",
    "porcelanato_60x60_premium": "ADHESIVO_PORCELANATO",
    "ceramico_pared_25x35": "ADHESIVO_CERAMICO",
    "ceramico_30x30": "ADHESIVO_CERAMICO",
    "ceramico_45x45": "ADHESIVO_CERAMICO",
}
ADHESIVO_M2_POR_BOLSA = Decimal("4")
ADHESIVO_PORCELANATO_M2_POR_BOLSA = Decimal("3")
JUNTA_M2_POR_KG = Decimal("3")


def _q(v: Decimal) -> Decimal:
    return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _partidas_superficie(sup_m2: float, material_key: str, tarea_mo: str, desc: str, datos: DatosEmpresa):
    if sup_m2 <= 0:
        return []
    sup = Decimal(str(sup_m2))
    cod_mat = CODIGO_MATERIAL.get(material_key, "PORCELANATO_60X60")
    cod_adh = CODIGO_ADHESIVO.get(material_key, "ADHESIVO_CERAMICO")
    es_porc = "porcelanato" in material_key
    m2_por_bolsa = ADHESIVO_PORCELANATO_M2_POR_BOLSA if es_porc else ADHESIVO_M2_POR_BOLSA
    cant_adh = ceil(sup / m2_por_bolsa)
    cant_junta = ceil(sup / JUNTA_M2_POR_KG)
    rend_mat = rendimiento(datos, cod_mat, Decimal("1.10"))
    cant_mat = _q(sup * rend_mat)
    costo_mo = precio_mano_obra(datos, tarea_mo) * sup
    return [
        Partida(concepto=desc + " material", cantidad=cant_mat, unidad="m2", precio_unitario=precio_material(datos, cod_mat), subtotal=cant_mat * precio_material(datos, cod_mat), categoria="material"),
        Partida(concepto="Adhesivo", cantidad=cant_adh, unidad="u", precio_unitario=precio_material(datos, cod_adh), subtotal=cant_adh * precio_material(datos, cod_adh), categoria="material"),
        Partida(concepto="Junta/pastina", cantidad=cant_junta, unidad="kg", precio_unitario=precio_material(datos, "JUNTA_PORCELANATO"), subtotal=cant_junta * precio_material(datos, "JUNTA_PORCELANATO"), categoria="material"),
        Partida(concepto="MO " + desc, cantidad=sup_m2, unidad="m2", precio_unitario=costo_mo / sup, subtotal=costo_mo, categoria="mano_obra"),
    ]


class CalcRevestimientoBanio:
    accion = "revestimiento_banio"
    schema_params = ParamsRevestimientoBanio

    @staticmethod
    def calcular(params: ParamsRevestimientoBanio, empresa_id: str) -> ResultadoPresupuesto:
        datos = cargar_empresa(empresa_id)
        partidas = []
        if params.superficie_piso_m2 > 0:
            partidas.extend(_partidas_superficie(params.superficie_piso_m2, params.material_piso, "PISO_CERAMICO", "Piso", datos))
        if params.superficie_pared_m2 > 0:
            partidas.extend(_partidas_superficie(params.superficie_pared_m2, params.material_pared, "REVESTIMIENTO_CERAMICO", "Pared", datos))
        if params.incluye_alzada_cocina and params.superficie_alzada_m2 > 0:
            partidas.extend(_partidas_superficie(params.superficie_alzada_m2, params.material_pared, "REVESTIMIENTO_CERAMICO", "Alzada", datos))
        materiales_faltantes(partidas, datos)
        total = sum((p.subtotal for p in partidas), Decimal("0"))
        sub_mat = sum((p.subtotal for p in partidas if p.categoria == "material"), Decimal("0"))
        sub_mo = sum((p.subtotal for p in partidas if p.categoria == "mano_obra"), Decimal("0"))
        return ResultadoPresupuesto(
            rubro="revestimiento_banio",
            partidas=partidas,
            subtotal_materiales=sub_mat,
            subtotal_mano_obra=sub_mo,
            total=total,
            metadata={"superficie_piso_m2": params.superficie_piso_m2, "superficie_pared_m2": params.superficie_pared_m2},
        )


registrar(CalcRevestimientoBanio())
