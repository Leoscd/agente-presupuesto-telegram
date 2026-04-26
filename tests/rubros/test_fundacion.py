"""Tests para src/rubros/fundacion.py"""
from __future__ import annotations
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.rubros.fundacion import ParamsFundacion
from src.rubros import REGISTRY

EMPRESA = "estudio_ramos"

def _calc(**kwargs):
    return REGISTRY["fundacion"].calcular(ParamsFundacion(**kwargs), EMPRESA)

class TestCasosBase:
    def test_zapata_aislada(self):
        r = _calc(tipo="zapata_aislada", largo_m=1.0, ancho_m=1.0, alto_m=0.5, cantidad=6)
        assert r.metadata["tipo"] == "zapata_aislada"
        assert r.total > 0

    def test_invariante_suma(self):
        r = _calc(tipo="zapata_aislada", largo_m=1.0, ancho_m=1.0, alto_m=0.5, cantidad=4)
        assert sum(p.subtotal for p in r.partidas) == r.total

    def test_partidas_positivas(self):
        r = _calc(tipo="zapata_aislada", largo_m=1.0, ancho_m=1.0, alto_m=0.5, cantidad=2)
        for p in r.partidas:
            assert p.subtotal > 0

class TestPropiedades:
    @given(cant=st.integers(min_value=1, max_value=20))
    @settings(max_examples=10)
    def test_idempotencia(self, cant):
        r1 = _calc(tipo="zapata_aislada", largo_m=1.0, ancho_m=1.0, alto_m=0.5, cantidad=cant)
        r2 = _calc(tipo="zapata_aislada", largo_m=1.0, ancho_m=1.0, alto_m=0.5, cantidad=cant)
        assert r1.total == r2.total