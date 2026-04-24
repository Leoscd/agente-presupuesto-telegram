"""Tests para src/rubros/cubierta_tejas.py"""
from __future__ import annotations

from decimal import Decimal

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

import src.rubros  # activa el registro
from src.rubros.cubierta_tejas import ParamsCubiertaTejas
from src.rubros.base import REGISTRY

EMPRESA = "estudio_ramos"


def _calc(**kwargs):
    calc = REGISTRY["cubierta_tejas"]
    params = ParamsCubiertaTejas(**kwargs)
    return calc.calcular(params, EMPRESA)


@pytest.fixture
def resultado_base():
    return _calc(ancho=5, largo=8, tipo_teja="ceramica_colonial", pendiente_pct=30)


class TestCasosBase:
    def test_teja_colonial_5x8(self, resultado_base):
        r = resultado_base
        # factor = sqrt(1 + 0.30^2) ≈ 1.044031
        # m2_real = q(5 * 8 * 1.044031) ≈ 41.76
        assert r.metadata["superficie_m2"] == pytest.approx(41.76, abs=0.01)
        # cant_tejas = ceil(41.76 * 16 * 1.10) = ceil(734.976) = 735
        tejas = next(p for p in r.partidas if "teja" in p.concepto.lower())
        assert tejas.cantidad == Decimal("735")

    def test_teja_cemento(self):
        r = _calc(ancho=6, largo=10, tipo_teja="cemento", pendiente_pct=25)
        tejas = next(p for p in r.partidas if "teja" in p.concepto.lower())
        # factor = sqrt(1 + 0.25^2) ≈ 1.030776; m2_real ≈ 61.85
        # cant_tejas = ceil(61.85 * 12 * 1.10) = ceil(816.42) = 817
        assert tejas.cantidad == Decimal("817")

    def test_invariante_suma_partidas_igual_total(self, resultado_base):
        assert sum(p.subtotal for p in resultado_base.partidas) == resultado_base.total

    def test_partidas_tienen_subtotales_positivos(self, resultado_base):
        for p in resultado_base.partidas:
            assert p.subtotal > 0

    def test_metadata_completa(self, resultado_base):
        assert "superficie_m2" in resultado_base.metadata
        assert "factor_pendiente" in resultado_base.metadata

    def test_factor_pendiente_mayor_da_mas_m2(self):
        """Mayor pendiente implica mayor superficie real y mayor total."""
        r_bajo = _calc(ancho=5, largo=8, pendiente_pct=20)
        r_alto = _calc(ancho=5, largo=8, pendiente_pct=45)
        assert r_alto.metadata["superficie_m2"] > r_bajo.metadata["superficie_m2"]
        assert r_alto.total > r_bajo.total

    def test_tipos_teja_producen_totales_distintos(self, resultado_base):
        r_cem = _calc(ancho=5, largo=8, tipo_teja="cemento", pendiente_pct=30)
        assert resultado_base.total != r_cem.total

    def test_partidas_esperadas(self, resultado_base):
        conceptos = [p.concepto.lower() for p in resultado_base.partidas]
        assert any("teja" in c for c in conceptos)
        assert any("liston" in c or "listón" in c for c in conceptos)
        assert any("cumbrera" in c for c in conceptos)
        assert len([p for p in resultado_base.partidas if p.categoria == "mano_obra"]) == 1


class TestValidacion:
    @pytest.mark.parametrize("pendiente", [14.9, 60.1, 0, -1])
    def test_pendiente_fuera_de_rango_falla(self, pendiente):
        with pytest.raises(Exception):
            _calc(ancho=5, largo=8, pendiente_pct=pendiente)

    @pytest.mark.parametrize("ancho,largo", [(-1, 8), (5, -1), (0, 8), (5, 0)])
    def test_dimensiones_invalidas_lanzan_error(self, ancho, largo):
        with pytest.raises(Exception):
            _calc(ancho=ancho, largo=largo)


class TestPropiedades:
    @given(ancho=st.floats(min_value=2.0, max_value=15.0),
           largo=st.floats(min_value=2.0, max_value=15.0))
    @settings(max_examples=30)
    def test_idempotencia(self, ancho, largo):
        r1 = _calc(ancho=ancho, largo=largo, tipo_teja="ceramica_colonial", pendiente_pct=30)
        r2 = _calc(ancho=ancho, largo=largo, tipo_teja="ceramica_colonial", pendiente_pct=30)
        assert r1.total == r2.total

    @given(ancho=st.floats(min_value=2.0, max_value=14.0))
    @settings(max_examples=30)
    def test_mas_superficie_mas_total(self, ancho):
        r1 = _calc(ancho=ancho, largo=8, tipo_teja="ceramica_colonial", pendiente_pct=30)
        r2 = _calc(ancho=ancho + 1.0, largo=8, tipo_teja="ceramica_colonial", pendiente_pct=30)
        assert r2.total >= r1.total


class TestGolden:
    """Valores calculados manualmente con precios de precios_materiales.csv y precios_mano_obra.csv."""

    def test_golden_cub_001_colonial_5x8_pend30(self):
        # factor=sqrt(1+0.09)≈1.044031; m2_real=q(5*8*1.044031)=41.76
        # cant_tejas=ceil(41.76*16*1.10)=735; cant_listones=ceil(41.76*1.2)=51
        # cant_cumbreras=ceil(8/0.30)=27
        # sub_mat = 735*850 + 51*4800 + 27*1200
        #         = 624750 + 244800 + 32400 = 901950
        # sub_mo = 6500*41.76 = 271440; total = 1173390
        r = _calc(ancho=5, largo=8, tipo_teja="ceramica_colonial", pendiente_pct=30)
        assert r.total == Decimal("1173390.00")

    def test_golden_cub_002_cemento_6x10_pend25(self):
        # factor=sqrt(1+0.0625)≈1.030776; m2_real=q(6*10*1.030776)=61.85
        # cant_tejas=ceil(61.85*12*1.10)=817; cant_listones=ceil(61.85*1.2)=75
        # cant_cumbreras=ceil(10/0.30)=34
        # sub_mat = 817*620 + 75*4800 + 34*1200
        #         = 506540 + 360000 + 40800 = 907340
        # sub_mo = 6500*61.85 = 402025; total = 1309365
        r = _calc(ancho=6, largo=10, tipo_teja="cemento", pendiente_pct=25)
        assert r.total == Decimal("1309365.00")
