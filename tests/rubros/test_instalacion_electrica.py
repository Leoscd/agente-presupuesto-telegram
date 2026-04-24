"""Tests para instalacion_electrica."""
from __future__ import annotations

from decimal import Decimal
import pytest
from hypothesis import given, strategies as st

from src.rubros import REGISTRY
from src.rubros.instalacion_electrica import ParamsInstalacionElectrica


EMPRESA = "estudio_ramos"


def _calc(**kwargs):
    params = ParamsInstalacionElectrica(**kwargs)
    return REGISTRY["instalacion_electrica"].calcular(params, EMPRESA)


def test_basica_50m2():
    """50m2, tipo basica, calcular bocas = ceil(50/4) = 13"""
    r = _calc(superficie_m2=50, tipo="basica")

    assert r.metadata["superficie_m2"] == 50
    assert r.metadata["cantidad_bocas"] == 13


def test_completa_con_bocas_definidas():
    """80m2, tipo completa, cantidad_bocas=20"""
    r = _calc(superficie_m2=80, tipo="completa", cantidad_bocas=20)

    assert r.metadata["cantidad_bocas"] == 20


def test_incluye_tablero():
    """Por defecto incluye_tablero=True"""
    r = _calc(superficie_m2=30, tipo="basica", incluye_tablero=True)
    
    # Debe tener tablero
    has_tablero = any("tablero" in p.concepto.lower() for p in r.partidas)
    assert has_tablero


def test_sin_tablero():
    """sin tablero"""
    r = _calc(superficie_m2=30, tipo="basica", incluye_tablero=False)
    
    has_tablero = any("tablero" in p.concepto.lower() for p in r.partidas)
    assert not has_tablero


def test_invariante_suma():
    r = _calc(superficie_m2=50, tipo="basica")
    suma = sum((p.subtotal for p in r.partidas), Decimal("0"))
    assert suma == r.total


@given(
    sup=st.floats(min_value=10, max_value=100),
)
def test_monotonia(sup):
    r1 = _calc(superficie_m2=sup, tipo="basica")
    r2 = _calc(superficie_m2=sup + 20, tipo="basica")
    assert r2.total >= r1.total