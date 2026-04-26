"""Tests para src/rubros/escalera_hormigon.py"""
from __future__ import annotations
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.rubros.escalera_hormigon import ParamsEscaleraHormigon
from src.rubros import REGISTRY

EMPRESA = "estudio_ramos"

def _calc(**kwargs):
    return REGISTRY["escalera_hormigon"].calcular(ParamsEscaleraHormigon(**kwargs), EMPRESA)

class TestCasosBase:
    def test_caso_base(self):
        r = _calc(cantidad_escalones=12, ancho_m=1.0, huella_cm=28, contrahuela_cm=18)
        assert r.metadata["cantidad_escalones"] == 12
        assert r.total > 0

    def test_invariante_suma(self):
        r = _calc(cantidad_escalones=15, ancho_m=1.0, huella_cm=28, contrahuela_cm=18)
        assert sum(p.subtotal for p in r.partidas) == r.total

    def test_partidas_positivas(self):
        r = _calc(cantidad_escalones=10, ancho_m=1.0, huella_cm=28, contrahuela_cm=18)
        for p in r.partidas:
            assert p.subtotal > 0

class TestPropiedades:
    @given(n=st.integers(min_value=4, max_value=20))
    @settings(max_examples=10)
    def test_idempotencia(self, n):
        r1 = _calc(cantidad_escalones=n, ancho_m=1.0, huella_cm=28, contrahuela_cm=18)
        r2 = _calc(cantidad_escalones=n, ancho_m=1.0, huella_cm=28, contrahuela_cm=18)
        assert r1.total == r2.total