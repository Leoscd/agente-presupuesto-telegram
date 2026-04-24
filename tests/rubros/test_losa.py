"""Tests determinísticos para losa sobre datos de estudio_ramos."""
from __future__ import annotations

from decimal import Decimal

import pytest
from hypothesis import given, strategies as st

from src.rubros import REGISTRY
from src.rubros.losa import ParamsLosa


EMPRESA = "estudio_ramos"


def _calc(**kwargs):
    params = ParamsLosa(**kwargs)
    return REGISTRY["losa"].calcular(params, EMPRESA)


def test_losa_4x5_12cm():
    """m3 = 4*5*0.12 = 2.4 m3. Cemento = ceil(2.4*7)=17"""
    r = _calc(ancho=4, largo=5, espesor_cm=12)

    assert r.metadata["superficie_m2"] == 20.0

    # Cemento: 2.4 * 7 = 16.8 -> ceil = 17
    cemento = next(p for p in r.partidas if "cemento" in p.concepto.lower())
    assert cemento.cantidad == 17


def test_espesor_default_es_12cm():
    """Sin pasar espesor_cm, debe usar 12 por defecto"""
    r = _calc(ancho=4, largo=5)  # sin espesor_cm

    assert r.metadata["volumen_m3"] == 2.4


def test_invariante_suma_partidas_igual_total():
    r = _calc(ancho=4, largo=5, espesor_cm=12)
    suma = sum((p.subtotal for p in r.partidas), Decimal("0"))
    assert suma == r.total


@given(
    ancho=st.decimals(min_value=Decimal("2"), max_value=Decimal("20"), places=1),
    largo=st.decimals(min_value=Decimal("2"), max_value=Decimal("20"), places=1),
)
def test_propiedad_monotonia(ancho, largo):
    """Más superficie => más total"""
    r1 = _calc(ancho=float(ancho), largo=float(largo))
    r2 = _calc(ancho=float(ancho) + 2, largo=float(largo))
    assert r2.total >= r1.total