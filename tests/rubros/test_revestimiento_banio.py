"""Tests determinísticos para revestimiento_banio sobre datos de estudio_ramos."""
from __future__ import annotations

from decimal import Decimal

import pytest
from hypothesis import given, strategies as st

from src.rubros import REGISTRY
from src.rubros.revestimiento_banio import ParamsRevestimientoBanio


EMPRESA = "estudio_ramos"


def _calc(**kwargs):
    params = ParamsRevestimientoBanio(**kwargs)
    return REGISTRY["revestimiento_banio"].calcular(params, EMPRESA)


def test_banio_completo_6m2_piso_18m2_pared():
    """Caso caso: total esperado = $698,700 ARS"""
    r = _calc(
        superficie_piso_m2=6,
        superficie_pared_m2=18,
        material_piso="porcelanato_60x60",
        material_pared="ceramico_pared_25x35"
    )

    # Debe tener partidas tanto de piso como de pared
    assert r.metadata["superficie_piso_m2"] == 6
    assert r.metadata["superficie_pared_m2"] == 18


def test_solo_piso():
    """Solo piso, sin paredes"""
    r = _calc(superficie_piso_m2=10, superficie_pared_m2=0)

    assert r.metadata["superficie_piso_m2"] == 10
    assert r.metadata["superficie_pared_m2"] == 0


def test_solo_pared():
    """Solo paredes, sin piso"""
    r = _calc(superficie_piso_m2=0, superficie_pared_m2=15)

    assert r.metadata["superficie_piso_m2"] == 0
    assert r.metadata["superficie_pared_m2"] == 15


def test_con_alzada_cocina():
    """Con alzada de cocina"""
    r = _calc(
        superficie_piso_m2=10,
        superficie_pared_m2=8,
        incluye_alzada_cocina=True,
        superficie_alzada_m2=4
    )

    assert r.metadata.get("incluye_alzada_cocina") is True


def test_sin_superficie_falla():
    """piso=0 y pared=0 debe lanzar ValidationError"""
    with pytest.raises(ValueError):
        _calc(superficie_piso_m2=0, superficie_pared_m2=0)


def test_invariante_suma_partidas():
    r = _calc(superficie_piso_m2=6, superficie_pared_m2=18)
    suma = sum((p.subtotal for p in r.partidas), Decimal("0"))
    assert suma == r.total


@given(
    piso=st.floats(min_value=0, max_value=20),
    pared=st.floats(min_value=0, max_value=30),
)
def test_propiedad_monotonia(piso, pared):
    if piso == 0 and pared == 0:
        return
    r1 = _calc(superficie_piso_m2=piso, superficie_pared_m2=pared)
    r2 = _calc(superficie_piso_m2=piso + 5, superficie_pared_m2=pared + 5)
    assert r2.total >= r1.total