"""Rubro: Cubierta de tejas.

Fórmulas:
- Superficie real con factor de pendiente
- Tejas con 10% desperdicio
- Listones: 1 cada 3 tejas de ancho
- Cumbreras: largo / 0.30m
- Mano de obra: precio_MO * m2
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from math import ceil, sqrt

from pydantic import BaseModel, Field, PositiveFloat

from src.datos.loader import (
    DatosEmpresa,
    cargar_empresa,
    precio_mano_obra,
    precio_material,
    rendimiento,
)
from src.datos.validador import materiales_faltantes
from src.rubros.base import Partida, ResultadoPresupuesto, registrar


class ParamsCubiertaTejas(BaseModel):
    ancho: PositiveFloat = Field(..., description="Metros")
    largo: PositiveFloat = Field(..., description="Metros")
    tipo_teja: str = Field("ceramica_colonial", description="Tipo de teja")
    pendiente_pct: float = Field(30.0, ge=15.0, le=60.0)


CODIGO_TEJA = {
    "ceramica_colonial": "TEJA_CERAMICA_COL",
    "cemento": "TEJA_CEMENTO",
}
TEJAS_POR_M2 = {
    "ceramica_colonial": Decimal("16"),
    "cemento": Decimal("12"),
}


def _q(v) -> Decimal:
    return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calcular(params: ParamsCubiertaTejas, empresa_id: str) -> ResultadoPresupuesto:
    datos = cargar_empresa(empresa_id)
    
    # Factor de pendiente
    factor = sqrt(1 + (Decimal(str(params.pendiente_pct)) / Decimal("100")) ** 2)
    m2_real = _q(Decimal(str(params.ancho)) * _q(Decimal(str(params.largo)) * factor

    cod_teja = CODIGO_TEJA.get(params.tipo_teja, "TEJA_CERAMICA_COL")
    
    # Tejas con 10% desperdicio
    cant_tejas = ceil(m2_real * TEJAS_POR_M2.get(params.tipo_teja, Decimal("16")) * Decimal("1.10"))

    # Listones: ~1 por m2
    cant_listones = ceil(m2_real * Decimal("1.2"))

    # Cumbreras
    cant_cumbreras = ceil(_q(Decimal(str(params.largo))) / Decimal("0.30"))

    # Mano de obra
    costo_mo = precio_mano_obra(datos, "CUBIERTA_TEJAS") * m2_real

    partidas = [
        Partida(concepto=f"Teja {params.tipo_teja}", cantidad=cant_tejas, unidad="u", precio_unitario=precio_material(datos, cod_teja), categoria="material"),
        Partida(concepto="Listón madera 2x3\" x 3m", cantidad=cant_listones, unidad="u", precio_unitario=precio_material(datos, "LISTON_MADERA_2X3"), categoria="material"),
        Partida(concepto="Cumbrera cerámica", cantidad=cant_cumbreras, unidad="u", precio_unitario=precio_material(datos, "CUMBRERA_CERAMICA"), categoria="material"),
        Partida(concepto="Mano de obra cubierta tejas", cantidad=float(m2_real), unidad="m2", precio_unitario=costo_mo / m2_real, categoria="mano_obra"),
    ]

    materiales_faltantes(partidas, datos)

    resultado = ResultadoPresupuesto(
        accion="cubierta_tejas",
        parametros=params.model_dump(),
        partidas=partidas,
        metadata={"superficie_m2": float(m2_real), "factor_pendiente": float(factor)},
    )

    return resultado


registrar("cubierta_tejas", ParamsCubiertaTejas, calcular)