"""Tests para src/rubros/losa.py"""
from __future__ import annotations

from decimal import Decimal

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

import src.rubros  # activa el registro
from src.rubros.losa import ParamsLosa
from src.rubros.base import REGISTRY

EMPRESA = "estudio_ramos"


def _calc(**kwargs):
    calc = REGISTRY["losa"]
    params = ParamsLosa(**kwargs)
    return calc.calcular(params, EMPRESA)


@pytest.fixture
def resultado_base():
    return _calc(ancho=4, largo=5, espesor_cm=12)


class TestCasosBase:
    def test_losa_4x5_espesor12(self, resultado_base):
        r = resultado_base
        assert r.metadata["superficie_m2"] == 20.0
        # m3 = 20 * 12 / 100 = 2.40
        assert r.metadata["volumen_m3"] == pytest.approx(2.40, abs=0.01)

        hierro = next(p for p in r.partidas if "hierro" in p.concepto.lower())
        # ceil(20 * 1.2) = 24
        assert hierro.cantidad == Decimal("24")

        cemento = next(p for p in r.partidas if "cemento" in p.concepto.lower())
        # ceil(2.40 * 7) = 17
        assert cemento.cantidad == Decimal("17")

    def test_espesor_minimo_8_funciona(self):
        r = _calc(ancho=3, largo=4, espesor_cm=8.0)
        assert r.total > 0
        assert r.metadata["superficie_m2"] == 12.0

    def test_invariante_suma_partidas_igual_total(self, resultado_base):
        assert sum(p.subtotal for p in resultado_base.partidas) == resultado_base.total

    def test_partidas_tienen_subtotales_positivos(self, resultado_base):
        for p in resultado_base.partidas:
            assert p.subtotal > 0

    def test_metadata_completa(self, resultado_base):
        assert "superficie_m2" in resultado_base.metadata
        assert "volumen_m3" in resultado_base.metadata


class TestValidacion:
    def test_espesor_menor_a_8_falla(self):
        with pytest.raises(Exception):
            _calc(ancho=4, largo=5, espesor_cm=7.9)

    def test_espesor_mayor_a_25_falla(self):
        with pytest.raises(Exception):
            _calc(ancho=4, largo=5, espesor_cm=25.1)

    @pytest.mark.parametrize("ancho,largo", [(-1, 5), (4, -1), (0, 5), (4, 0)])
    def test_dimensiones_invalidas_lanzan_error(self, ancho, largo):
        with pytest.raises(Exception):
            _calc(ancho=ancho, largo=largo, espesor_cm=12)


class TestPropiedades:
    @given(ancho=st.floats(min_value=1.0, max_value=15.0),
           largo=st.floats(min_value=1.0, max_value=15.0))
    @settings(max_examples=30)
    def test_idempotencia(self, ancho, largo):
        r1 = _calc(ancho=ancho, largo=largo, espesor_cm=12)
        r2 = _calc(ancho=ancho, largo=largo, espesor_cm=12)
        assert r1.total == r2.total

    @given(espesor=st.floats(min_value=8.0, max_value=24.0))
    @settings(max_examples=30)
    def test_mas_espesor_mas_materiales(self, espesor):
        """Mayor espesor implica más volumen y más materiales."""
        r1 = _calc(ancho=4, largo=5, espesor_cm=espesor)
        r2 = _calc(ancho=4, largo=5, espesor_cm=espesor + 1.0)
        assert r2.subtotal_materiales >= r1.subtotal_materiales


class TestGolden:
    """Valores calculados manualmente con precios de precios_materiales.csv y precios_mano_obra.csv."""

    def test_golden_losa_001_4x5_esp12(self):
        # m2=20, m3=2.40
        # cemento=ceil(2.40*7)=17; arena=2.40*0.45=1.08; piedra=2.40*0.65=1.56
        # hierro8=ceil(20*1.2)=24; plast=max(1,ceil(2.40/15))=1
        # sub_mat = 17*12500+1.08*38000+1.56*45000+24*9500+1*18500
        #         = 212500+41040+70200+228000+18500 = 570240
        # sub_mo = 28500*20 = 570000; total = 1140240
        r = _calc(ancho=4, largo=5, espesor_cm=12)
        assert r.total == Decimal("1140240.00")

    def test_golden_losa_002_6x8_esp15(self):
        # m2=48, m3=7.20
        # cemento=ceil(7.20*7)=51; arena=7.20*0.45=3.24; piedra=7.20*0.65=4.68
        # hierro8=ceil(48*1.2)=58; plast=max(1,ceil(7.20/15))=1
        # sub_mat = 51*12500+3.24*38000+4.68*45000+58*9500+1*18500
        #         = 637500+123120+210600+551000+18500 = 1540720
        # sub_mo = 28500*48 = 1368000; total = 2908720
        r = _calc(ancho=6, largo=8, espesor_cm=15)
        assert r.total == Decimal("2908720.00")

    def test_golden_losa_003_3x4_esp8(self):
        # m2=12, m3=0.96
        # cemento=ceil(0.96*7)=7; arena=0.96*0.45=0.43; piedra=0.96*0.65=0.62
        # hierro8=ceil(12*1.2)=15; plast=max(1,ceil(0.96/15))=1
        # sub_mat = 7*12500+0.43*38000+0.62*45000+15*9500+1*18500
        #         = 87500+16340+27900+142500+18500 = 292740 (note: 0.43*38000=16340, 0.62*45000=27900)
        # sub_mo = 28500*12 = 342000; total = 634740
        r = _calc(ancho=3, largo=4, espesor_cm=8)
        assert r.total == Decimal("634740.00")
