"""Tests para src/rubros/viga_encadenado.py"""
from __future__ import annotations
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.rubros.viga_encadenado import ParamsVigaEncadenado
from src.rubros import REGISTRY

EMPRESA = "estudio_ramos"

def _calc(**kwargs):
    return REGISTRY["viga_encadenado"].calcular(ParamsVigaEncadenado(**kwargs), EMPRESA)

class TestCasosBase:
    def test_caso_base(self):
        r = _calc(longitud_ml=10.0, base_cm=20, alto_cm=30, tipo="encadenado")
        assert r.total > 0

    def test_invariante_suma(self):
        r = _calc(longitud_ml=15.0, base_cm=25, alto_cm=40, tipo="encadenado")
        assert sum(p.subtotal for p in r.partidas) == r.total

    def test_partidas_positivas(self):
        r = _calc(longitud_ml=8.0, base_cm=20, alto_cm=30, tipo="encadenado")
        for p in r.partidas:
            assert p.subtotal > 0

class TestPropiedades:
    @given(ml=st.floats(min_value=1.0, max_value=50.0))
    @settings(max_examples=10)
    def test_idempotencia(self, ml):
        r1 = _calc(longitud_ml=ml, base_cm=20, alto_cm=30, tipo="encadenado")
        r2 = _calc(longitud_ml=ml, base_cm=20, alto_cm=30, tipo="encadenado")
        assert r1.total == r2.total