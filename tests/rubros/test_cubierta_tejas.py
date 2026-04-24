"""Tests determinísticos para cubierta_tejas sobre datos de estudio_ramos."""
from __future__ import annotations

from decimal import Decimal
from math import sqrt

import pytest
from hypothesis import given, strategies as st

from src.rubros import REGISTRY
from src.rubros.cubierta_tejas import ParamsCubiertaTejas


EMPRESA = "estudio_ramos"


def _calc(**kwargs):
    params = ParamsCubiertaTejas(**kwargs)
    return REGISTRY["cubierta_tejas"].calcular(params, EMPRESA)


def test_teja_ceramica_5x8_30pct():
    """5x8=40m2, factor=sqrt(1+0.3²)=1.044, m2_real≈41.76
    tejas = ceil(41.76*16*1.10)=735"""
    r = _calc(ancho=5, largo=8, pendiente_pct=30, tipo_teja="ceramica_colonial")

    factor = sqrt(1 + 0.3**2)
    m2_real = 5 * 8 * factor

    assert abs(r.metadata["superficie_m2"] - m2_real) < 1


def test_teja_cemento_vs_ceramica():
    """Misma superficie, teja cemento más barata"""
    r_ceramica = _calc(ancho=4, largo=6, tipo_teja="ceramica_colonial")
    r_cemento = _calc(ancho=4, largo=6, tipo_teja="cemento")

    # Debe ser más barato porque teja cemento es más económica
    assert r_cemento.total < r_ceramica.total


def test_invariante_suma_partidas():
    r = _calc(ancho=5, largo=8, pendiente_pct=30, tipo_teja="ceramica_colonial")
    suma = sum((p.subtotal for p in r.partidas), Decimal("0"))
    assert suma == r.total


@given(
    ancho=st.floats(min_value=2.0, max_value=15.0),
    largo=st.floats(min_value=2.0, max_value=20.0),
)
def test_propiedad_monotonia(ancho, largo):
    r1 = _calc(ancho=ancho, largo=largo)
    r2 = _calc(ancho=ancho + 2, largo=largo)
    assert r2.total >= r1.total