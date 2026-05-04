"""Tests para src/rubros/estructura_metalica.py"""
from __future__ import annotations
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.rubros.estructura_metalica import ParamsEstructuraMetalica
from src.rubros import REGISTRY

EMPRESA = "estudio_ramos"

def _calc(**kwargs):
    return REGISTRY["estructura_metalica"].calcular(ParamsEstructuraMetalica(**kwargs), EMPRESA)

class TestCasosBase:
    def test_caso_base(self):
        r = _calc(longitud_ml=50.0, tipo_perfil="IPN_120", incluye_pintura_anticorrosiva=True)
        assert r.total > 0

    def test_invariante_suma(self):
        r = _calc(longitud_ml=50.0, tipo_perfil="IPN_120", incluye_pintura_anticorrosiva=True)
        assert sum(p.subtotal for p in r.partidas) == r.total

    def test_partidas_positivas(self):
        r = _calc(longitud_ml=50.0, tipo_perfil="IPN_120", incluye_pintura_anticorrosiva=True)
        for p in r.partidas:
            assert p.subtotal > 0

class TestPropiedades:
    @given(ml=st.floats(min_value=1.0, max_value=100.0))
    @settings(max_examples=10)
    def test_idempotencia(self, ml):
        r1 = _calc(longitud_ml=ml, tipo_perfil="IPN_120", incluye_pintura_anticorrosiva=True)
        r2 = _calc(longitud_ml=ml, tipo_perfil="IPN_120", incluye_pintura_anticorrosiva=True)
        assert r1.total == r2.total