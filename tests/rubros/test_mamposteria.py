"""Tests para src/rubros/mamposteria.py"""
from __future__ import annotations

from decimal import Decimal

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

import src.rubros  # activa el registro
from src.rubros.mamposteria import ParamsMamposteria
from src.rubros.base import REGISTRY

EMPRESA = "estudio_ramos"


def _calc(**kwargs):
    calc = REGISTRY["mamposteria"]
    params = ParamsMamposteria(**kwargs)
    return calc.calcular(params, EMPRESA)


@pytest.fixture
def resultado_base():
    return _calc(largo=5, alto=3, tipo="hueco_12")


class TestCasosBase:
    def test_muro_hueco12_5x3(self, resultado_base):
        r = resultado_base
        assert r.metadata["superficie_m2"] == 15.0

        ladrillos = next(p for p in r.partidas if "ladrillo" in p.concepto.lower())
        # ceil(15 * 36 * 1.05) = ceil(567.0) = 567
        assert ladrillos.cantidad == Decimal("567")

        cemento = next(p for p in r.partidas if "cemento" in p.concepto.lower())
        # ceil(15 / 10) = 2
        assert cemento.cantidad == Decimal("2")

    def test_invariante_suma_partidas_igual_total(self, resultado_base):
        r = resultado_base
        assert sum(p.subtotal for p in r.partidas) == r.total

    def test_partidas_tienen_subtotales_positivos(self, resultado_base):
        for p in resultado_base.partidas:
            assert p.subtotal > 0

    def test_metadata_completa(self, resultado_base):
        assert "superficie_m2" in resultado_base.metadata

    def test_tipos_ladrillo_producen_totales_distintos(self):
        r_h12 = _calc(largo=5, alto=3, tipo="hueco_12")
        r_h18 = _calc(largo=5, alto=3, tipo="hueco_18")
        r_com = _calc(largo=5, alto=3, tipo="comun")
        # Los tres tipos deben dar totales distintos
        assert r_h12.total != r_h18.total
        assert r_h12.total != r_com.total
        assert r_h18.total != r_com.total


class TestValidacion:
    @pytest.mark.parametrize("largo,alto", [(-1, 3), (5, -1), (0, 3), (5, 0)])
    def test_dimensiones_invalidas_lanzan_error(self, largo, alto):
        with pytest.raises(Exception):
            _calc(largo=largo, alto=alto)


class TestPropiedades:
    @given(largo=st.floats(min_value=1.0, max_value=20.0),
           alto=st.floats(min_value=1.0, max_value=5.0))
    @settings(max_examples=30)
    def test_idempotencia(self, largo, alto):
        r1 = _calc(largo=largo, alto=alto)
        r2 = _calc(largo=largo, alto=alto)
        assert r1.total == r2.total

    @given(largo=st.floats(min_value=1.0, max_value=20.0))
    @settings(max_examples=30)
    def test_mas_m2_mas_total(self, largo):
        """Más metros de muro implica mayor total."""
        r1 = _calc(largo=largo, alto=2.5)
        r2 = _calc(largo=largo + 1.0, alto=2.5)
        assert r2.total >= r1.total


class TestGolden:
    """Valores calculados manualmente con precios de precios_materiales.csv y precios_mano_obra.csv."""

    def test_golden_mamp_001_hueco12_5x3(self):
        # m2=15; ladrillos=ceil(15*36*1.05)=567; cemento=ceil(15/10)=2
        # plast=ceil(15*0.04)=1; arena=15*0.03=0.45
        # sub_mat = 567*520 + 2*12500 + 1*18500 + 0.45*38000 = 354840+25000+18500+17100 = ...
        # sub_mat = 294840+25000+18500+17100 = 355440
        # sub_mo = 8500*15 = 127500
        # total = 482940
        r = _calc(largo=5, alto=3, tipo="hueco_12")
        assert r.total == Decimal("482940.00")

    def test_golden_mamp_002_hueco18_10x2_8(self):
        # m2=28; ladrillos=ceil(28*28*1.05)=824; cemento=ceil(28/10)=3
        # plast=ceil(28*0.04)=2; arena=28*0.03=0.84
        # sub_mat = 824*780+3*12500+2*18500+0.84*38000 = 642720+37500+37000+31920 = 749140
        # sub_mo = 11200*28 = 313600; total = 1062740
        r = _calc(largo=10, alto=2.8, tipo="hueco_18")
        assert r.total == Decimal("1062740.00")

    def test_golden_mamp_003_comun_8x3(self):
        # m2=24; ladrillos=ceil(24*48*1.08)=ceil(1244.16)=1245 (rendimiento LADRILLO_COMUN=1.08)
        # cemento=ceil(24/10)=3; plast=ceil(24*0.04)=1; arena=24*0.03=0.72
        # sub_mat = 1245*180+3*12500+1*18500+0.72*38000 = 224100+37500+18500+27360 = 307460
        # sub_mo = 9800*24 = 235200; total = 542660
        r = _calc(largo=8, alto=3, tipo="comun")
        assert r.total == Decimal("542660.00")
