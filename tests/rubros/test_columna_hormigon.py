"""Tests para src/rubros/columna_hormigon.py"""
from __future__ import annotations
from decimal import Decimal
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.rubros.columna_hormigon import ParamsColumnaHormigon
from src.rubros import REGISTRY

EMPRESA = "estudio_ramos"

def _calc(**kwargs):
    return REGISTRY["columna_hormigon"].calcular(ParamsColumnaHormigon(**kwargs), EMPRESA)

class TestCasosBase:
    def test_caso_base(self):
        r = _calc(seccion="25x25", altura_m=3.0, cantidad=4)
        assert r.metadata["seccion"] == "25x25"
        assert r.total > 0

    def test_invariante_suma(self):
        r = _calc(seccion="30x30", altura_m=2.5, cantidad=2)
        assert sum(p.subtotal for p in r.partidas) == r.total

    def test_partidas_positivas(self):
        r = _calc(seccion="20x20", altura_m=3.0, cantidad=1)
        for p in r.partidas:
            assert p.subtotal > 0

class TestValidacion:
    def test_altura_minima(self):
        with pytest.raises(Exception):
            _calc(seccion="25x25", altura_m=1.5)

class TestPropiedades:
    @given(altura=st.floats(min_value=2.0, max_value=12.0), cant=st.integers(min_value=1, max_value=10))
    @settings(max_examples=10)
    def test_idempotencia(self, altura, cant):
        r1 = _calc(seccion="25x25", altura_m=altura, cantidad=cant)
        r2 = _calc(seccion="25x25", altura_m=altura, cantidad=cant)
        assert r1.total == r2.total