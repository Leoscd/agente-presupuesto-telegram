"""Rubro: Cielorraso de Durlock."""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from math import ceil

from pydantic import BaseModel, Field, PositiveFloat

from src.datos.loader import (
    cargar_empresa,
    precio_mano_obra,
    precio_material,
)
from src.datos.validador import materiales_faltantes
from src.rubros.base import Partida, ResultadoPresupuesto, registrar


class ParamsCielorraso(BaseModel):
    superficie_m2: PositiveFloat
    tipo: str = Field(default="simple", pattern="^(simple|doble)$")
    con_estructura: bool = True


def _q(v: Decimal) -> Decimal:
    return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# Constantes
M2_POR_PLACA = Decimal("2.88")   # 1.20m x 2.40m
ML_MONT_POR_M2 = Decimal("2.50")  # ml de montante por m2 (1 cada 40cm)
ML_SOL_POR_M2 = Decimal("0.60")  # ml de solera por m2
M2_POR_BOLSA_MAS = Decimal("20")  # m2 de masilla por bolsa
TORN_POR_PLACA = 25               # tornillos por placa


class _CalcCielorraso:
    accion = "cielorraso_durlock"
    schema_params = ParamsCielorraso

    def calcular(self, params: ParamsCielorraso, empresa_id: str) -> ResultadoPresupuesto:
        datos = cargar_empresa(empresa_id)

        codigos_usados = ["PLACA_DURLOCK_12", "MASILLA_DURLOCK", "TORNILLO_DURLOCK"]
        if params.con_estructura:
            codigos_usados += ["PERFIL_MONTANTE_70", "PERFIL_SOLERA_70"]
        faltantes = materiales_faltantes(datos, codigos_usados)
        if faltantes:
            raise ValueError(
                f"Materiales no disponibles en {empresa_id}: {', '.join(faltantes)}"
            )
        sup = Decimal(str(params.superficie_m2))
        capas = 2 if params.tipo == "doble" else 1

        # Placas (1.10 descarte)
        cant_placas = Decimal(ceil((sup * Decimal("1.10")) / M2_POR_PLACA)) * Decimal(str(capas))
        pu_placa = precio_material(datos, "PLACA_DURLOCK_12")
        sub_placa = _q(pu_placa * cant_placas)

        partidas = [
            Partida(
                concepto="Placa Durlock 12mm",
                cantidad=cant_placas,
                unidad="u",
                precio_unitario=pu_placa,
                subtotal=sub_placa,
                categoria="material",
            ),
        ]

        subtotal_materiales = sub_placa

        # Perfiles (solo si con_estructura)
        if params.con_estructura:
            total_ml_mont = sup * ML_MONT_POR_M2
            cant_montantes = Decimal(ceil(total_ml_mont / Decimal("3")))  # Perfil 3m
            pu_mont = precio_material(datos, "PERFIL_MONTANTE_70")
            sub_mont = _q(pu_mont * cant_montantes)

            total_ml_sol = sup * ML_SOL_POR_M2
            cant_soleras = Decimal(ceil(total_ml_sol / Decimal("3")))
            pu_sol = precio_material(datos, "PERFIL_SOLERA_70")
            sub_sol = _q(pu_sol * cant_soleras)

            partidas.extend([
                Partida(concepto="Perfil montante 70mm", cantidad=cant_montantes, unidad="u",
                      precio_unitario=pu_mont, subtotal=sub_mont, categoria="material"),
                Partida(concepto="Perfil solera 70mm", cantidad=cant_soleras, unidad="u",
                      precio_unitario=pu_sol, subtotal=sub_sol, categoria="material"),
            ])
            subtotal_materiales += sub_mont + sub_sol

        # Masilla
        cant_bolsas_mas = Decimal(ceil(sup / M2_POR_BOLSA_MAS))
        pu_mas = precio_material(datos, "MASILLA_DURLOCK")
        sub_mas = _q(pu_mas * cant_bolsas_mas)
        partidas.append(Partida(concepto="Masilla Durlock bolsa 25kg", cantidad=cant_bolsas_mas,
                              unidad="u", precio_unitario=pu_mas, subtotal=sub_mas, categoria="material"))
        subtotal_materiales += sub_mas

        # Tornillos
        cant_torn_total = int(cant_placas) * TORN_POR_PLACA
        cant_bolsas_torn = Decimal(ceil(cant_torn_total / 500))
        pu_torn = precio_material(datos, "TORNILLO_DURLOCK")
        sub_torn = _q(pu_torn * cant_bolsas_torn)
        partidas.append(Partida(concepto="Tornillo Durlock bolsa 500u", cantidad=cant_bolsas_torn,
                              unidad="u", precio_unitario=pu_torn, subtotal=sub_torn, categoria="material"))
        subtotal_materiales += sub_torn

        # MO
        p_mo = precio_mano_obra(datos, "CIELORRASO_DURLOCK")
        costo_mo = _q(p_mo * sup)
        partidas.append(Partida(concepto="MO cielorraso Durlock", cantidad=sup, unidad="m2",
                              precio_unitario=p_mo, subtotal=costo_mo, categoria="mano_obra"))

        total = subtotal_materiales + costo_mo

        return ResultadoPresupuesto(
            rubro="cielorraso_durlock",
            metadata={
                "superficie_m2": params.superficie_m2,
                "tipo": params.tipo,
                "con_estructura": params.con_estructura,
            },
            partidas=partidas,
            subtotal_materiales=_q(subtotal_materiales),
            subtotal_mano_obra=_q(costo_mo),
            total=_q(total),
            advertencias=[],
        )


registrar(_CalcCielorraso())