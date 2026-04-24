"""Rubro: Piso cerámico / porcelanato."""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from math import ceil

from pydantic import BaseModel, Field, PositiveFloat

from src.datos.loader import (
    cargar_empresa,
    precio_mano_obra,
    precio_material,
    rendimiento,
)
from src.rubros.base import Partida, ResultadoPresupuesto, registrar


class ParamsPisoCeramico(BaseModel):
    superficie_m2: PositiveFloat
    material: str = Field(
        default="ceramico_45x45", pattern="^ceramico_(30x30|45x45)$|^porcelanato_60x60(_premium)?$"
    )
    incluye_zocalo: bool = False
    perimetro_m: float = Field(default=0.0, ge=0.0)


def _q(v: Decimal) -> Decimal:
    return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


CODIGO_MATERIAL = {
    "ceramico_30x30": "CERAMICO_30X30",
    "ceramico_45x45": "CERAMICO_45X45",
    "porcelanato_60x60": "PORCELANATO_60X60",
    "porcelanato_60x60_premium": "PORCELANATO_60X60_PREMIUM",
}
CODIGO_ADHESIVO = {
    "ceramico_30x30": "ADHESIVO_CERAMICO",
    "ceramico_45x45": "ADHESIVO_CERAMICO",
    "porcelanato_60x60": "ADHESIVO_PORCELANATO",
    "porcelanato_60x60_premium": "ADHESIVO_PORCELANATO",
}
ADHESIVO_M2_POR_BOLSA = Decimal("4")
ADHESIVO_PORC_M2_POR_BOLSA = Decimal("3")
JUNTA_M2_POR_KG = Decimal("3")


class CalcPisoCeramico:
    accion = "piso_ceramico"
    schema_params = ParamsPisoCeramico

    @staticmethod
    def calcular(params: ParamsPisoCeramico, empresa_id: str) -> ResultadoPresupuesto:
        datos = cargar_empresa(empresa_id)

        sup = _q(Decimal(str(params.superficie_m2)))
        es_porc = "porcelanato" in params.material
        m2_por_bolsa = ADHESIVO_PORC_M2_POR_BOLSA if es_porc else ADHESIVO_M2_POR_BOLSA

        cod_mat = CODIGO_MATERIAL[params.material]
        cod_adh = CODIGO_ADHESIVO[params.material]

        # Material de piso
        cant_mat = _q(sup * rendimiento(datos, cod_mat, Decimal("1.10")))
        pu_mat = precio_material(datos, cod_mat)
        subtotal_mat = _q(pu_mat * cant_mat)

        # Adhesivo
        cant_adhesivo = Decimal(ceil(sup / m2_por_bolsa))
        pu_adh = precio_material(datos, cod_adh)
        subtotal_adh = _q(pu_adh * cant_adhesivo)

        # Pastina/junta
        cant_junta = Decimal(ceil(sup / JUNTA_M2_POR_KG))
        pu_junta = precio_material(datos, "JUNTA_PORCELANATO")
        subtotal_junta = _q(pu_junta * cant_junta)

        # MO colocación piso
        p_mo = precio_mano_obra(datos, "PISO_CERAMICO")
        costo_mo = _q(p_mo * sup)

        partidas = [
            Partida(concepto=f"Piso {params.material} m2", cantidad=cant_mat, unidad="m2",
                  precio_unitario=pu_mat, subtotal=subtotal_mat, categoria="material"),
            Partida(concepto=f"Adhesivo {params.material}", cantidad=cant_adhesivo, unidad="u",
                  precio_unitario=pu_adh, subtotal=subtotal_adh, categoria="material"),
            Partida(concepto="Pastina/junta", cantidad=cant_junta, unidad="kg",
                  precio_unitario=pu_junta, subtotal=subtotal_junta, categoria="material"),
            Partida(concepto="MO colocación piso", cantidad=sup, unidad="m2",
                  precio_unitario=p_mo, subtotal=costo_mo, categoria="mano_obra"),
        ]

        subtotal_materiales = subtotal_mat + subtotal_adh + subtotal_junta
        subtotal_mo = costo_mo
        total = subtotal_materiales + subtotal_mo

        # Zócalo (solo si aplica)
        if params.incluye_zocalo and params.perimetro_m > 0:
            perim = _q(Decimal(str(params.perimetro_m)))
            cant_zocalo = _q(perim * rendimiento(datos, "ZOCALO_CERAMICO", Decimal("1.05")))
            pu_zocalo = precio_material(datos, "ZOCALO_CERAMICO")
            sub_zocalo = _q(pu_zocalo * cant_zocalo)

            # MO zócalo
            costo_mo_zoc = _q(p_mo * perim * Decimal("0.3"))

            partidas.extend([
                Partida(concepto="Zócalo cerámico", cantidad=cant_zocalo, unidad="ml",
                      precio_unitario=pu_zocalo, subtotal=sub_zocalo, categoria="material"),
                Partida(concepto="MO zócalo", cantidad=perim, unidad="ml",
                      precio_unitario=_q(p_mo * Decimal("0.3")), subtotal=costo_mo_zoc,
                      categoria="mano_obra"),
            ])

            subtotal_materiales += sub_zocalo
            subtotal_mo += costo_mo_zoc
            total += sub_zocalo + costo_mo_zoc

        return ResultadoPresupuesto(
            rubro="piso_ceramico",
            action="piso_ceramico",
            metadata={
                "superficie_m2": params.superficie_m2,
                "material": params.material,
                "incluye_zocalo": params.incluye_zocalo,
                "perimetro_m": params.perimetro_m,
            },
            partidas=partidas,
            subtotal_materiales=subtotal_materiales,
            subtotal_mano_obra=subtotal_mo,
            total=total,
            advertencias=[],
        )


registrar(CalcPisoCeramico())