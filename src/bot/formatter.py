"""Formato de texto para Telegram (MarkdownV2-safe)."""
from __future__ import annotations

from decimal import Decimal

from src.rubros.base import ResultadoPresupuesto


_ESCAPE = r"_*[]()~`>#+-=|{}.!\\"


def esc(s: str) -> str:
    return "".join("\\" + c if c in _ESCAPE else c for c in s)


def moneda(v: Decimal | float) -> str:
    d = Decimal(str(v)).quantize(Decimal("0.01"))
    entero, _, dec = f"{abs(d):.2f}".partition(".")
    partes = []
    while len(entero) > 3:
        partes.insert(0, entero[-3:])
        entero = entero[:-3]
    partes.insert(0, entero)
    signo = "-" if d < 0 else ""
    return f"{signo}$ {'.'.join(partes)},{dec}"


def formatear_presupuesto(r: ResultadoPresupuesto, id_corto: str) -> str:
    header = f"*{esc(r.rubro)}*  `{esc(id_corto)}`"
    meta = ""
    if r.metadata.get("superficie_m2"):
        meta = f"\n_Superficie: {esc(str(r.metadata['superficie_m2']))} m²_"

    lineas: list[str] = []
    for p in r.partidas:
        cant = str(p.cantidad).rstrip("0").rstrip(".")
        lineas.append(
            f"• {esc(p.concepto)} — {esc(cant)} {esc(p.unidad)} × {esc(moneda(p.precio_unitario))} "
            f"\\= *{esc(moneda(p.subtotal))}*"
        )
    body = "\n".join(lineas)

    resumen = (
        f"\n\n_Materiales:_ {esc(moneda(r.subtotal_materiales))}"
        f"\n_Mano de obra:_ {esc(moneda(r.subtotal_mano_obra))}"
        f"\n*TOTAL:* {esc(moneda(r.total))}"
    )
    advs = ""
    if r.advertencias:
        advs = "\n\n⚠️ " + "\n⚠️ ".join(esc(a) for a in r.advertencias)

    return f"{header}{meta}\n\n{body}{resumen}{advs}"
