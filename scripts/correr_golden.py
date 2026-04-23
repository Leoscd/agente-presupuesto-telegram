"""Corre el golden dataset y reporta desviaciones.

Uso:
    python -m scripts.correr_golden              # usa umbrales por defecto
    python -m scripts.correr_golden --strict     # falla si alguno supera umbral
"""
from __future__ import annotations

import argparse
import sys
from decimal import Decimal
from pathlib import Path

import yaml

# Dummy env antes de importar src.*
import os
ROOT = Path(__file__).resolve().parent.parent
os.environ.setdefault("TELEGRAM_TOKEN", "x")
os.environ.setdefault("MINIMAX_API_KEY", "x")

from src.rubros import REGISTRY  # noqa: E402
from src.rubros.base import ResultadoPresupuesto  # noqa: E402

GOLDEN_PATH = ROOT / "tests" / "golden" / "casos.yaml"
UMBRAL_TOTAL = 0.02      # 2%
UMBRAL_PARTIDA = 0.05    # 5%


def _cargar_casos() -> list[dict]:
    return list(yaml.safe_load(GOLDEN_PATH.read_text(encoding="utf-8")))


def _evaluar(caso: dict) -> tuple[bool, list[str]]:
    accion = caso["accion"]
    calc = REGISTRY[accion]
    params = calc.schema_params(**caso["parametros"])
    r: ResultadoPresupuesto = calc.calcular(params, caso["empresa"])

    fallos: list[str] = []
    esperado_total = Decimal(str(caso["esperado"]["total"]))
    delta = (r.total - esperado_total) / esperado_total if esperado_total else Decimal("0")
    if abs(delta) > Decimal(str(UMBRAL_TOTAL)):
        fallos.append(
            f"total {float(delta)*100:+.2f}% (calc={r.total} vs esp={esperado_total})"
        )

    for esp_part in caso["esperado"].get("partidas_clave", []):
        substr = esp_part["concepto_contiene"].lower()
        sub_esp = Decimal(str(esp_part["subtotal"]))
        halladas = [p for p in r.partidas if substr in p.concepto.lower()]
        if not halladas:
            fallos.append(f"falta partida con '{substr}'")
            continue
        sub_calc = halladas[0].subtotal
        dp = (sub_calc - sub_esp) / sub_esp if sub_esp else Decimal("0")
        if abs(dp) > Decimal(str(UMBRAL_PARTIDA)):
            fallos.append(
                f"partida '{substr}' {float(dp)*100:+.2f}% (calc={sub_calc} vs esp={sub_esp})"
            )

    return (len(fallos) == 0), fallos


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true", help="exit code != 0 si algún caso falla")
    args = parser.parse_args()

    casos = _cargar_casos()
    ok = 0
    fail = 0
    for caso in casos:
        passed, fallos = _evaluar(caso)
        marker = "✅" if passed else "❌"
        print(f"{marker} {caso['id']:14} {caso['descripcion']}")
        if not passed:
            for f in fallos:
                print(f"    · {f}")
        ok += passed
        fail += not passed

    print(f"\n{ok} ok / {fail} fail / {len(casos)} total")
    return 1 if (fail and args.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
