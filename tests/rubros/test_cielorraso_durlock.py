"""Tests para src/rubros/cielorraso_durlock.py"""
from __future__ import annotations
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.rubros.cielorraso_durlock import ParamsCielorraso
from src.rubros import REGISTRY

EMPRESA = "estudio_ramos"

def _calc(**kwargs):
    return REGISTRY["cielorraso_durlock"].calcular(ParamsCielorraso(**kwargs), EMPRESA)

class TestCasosBase:
    def test_simple(self):
        r = _calc(superficie_m2=20.0, tipo="simple", con_estructura=True)
        assert r.total > 0

    def test_doble(self):
        r = _calc(superficie_m2=20.0, tipo="doble", con_estructura=True)
        assert r.metadata["tipo"] == "doble"

    def test_invariante_suma(self):
        r = _calc(superficie_m2=20.0, tipo="simple", con_estructura=True)
        assert sum(p.subtotal for p in r.partidas) == r.total

    def test_partidas_positivas(self):
        r = _calc(superficie_m2=20.0, tipo="simple", con_estructura=True)
        for p in r.partidas:
            assert p.subtotal > 0

class TestPropiedades:
    @given(sup=st.floats(min_value=5.0, max_value=100.0))
    @settings(max_examples=10)
    def test_idempotencia(self, sup):
        r1 = _calc(superficie_m2=sup, tipo="simple", con_estructura=True)
        r2 = _calc(superficie_m2=sup, tipo="simple", con_estructura=True)
        assert r1.total == r2.total