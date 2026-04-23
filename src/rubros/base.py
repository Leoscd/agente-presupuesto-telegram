from __future__ import annotations

from decimal import Decimal
from typing import Literal, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

Categoria = Literal["material", "mano_obra", "equipo"]


class Partida(BaseModel):
    model_config = ConfigDict(frozen=True)

    concepto: str
    cantidad: Decimal
    unidad: str
    precio_unitario: Decimal
    subtotal: Decimal
    categoria: Categoria


class ResultadoPresupuesto(BaseModel):
    rubro: str
    partidas: list[Partida]
    subtotal_materiales: Decimal
    subtotal_mano_obra: Decimal
    subtotal_equipo: Decimal = Decimal("0")
    total: Decimal
    metadata: dict = Field(default_factory=dict)
    advertencias: list[str] = Field(default_factory=list)

    def model_post_init(self, __context) -> None:  # type: ignore[override]
        suma = sum((p.subtotal for p in self.partidas), Decimal("0"))
        if abs(suma - self.total) > Decimal("0.01"):
            raise ValueError(
                f"Invariante roto: sum(partidas.subtotal)={suma} != total={self.total}"
            )


@runtime_checkable
class Calculadora(Protocol):
    accion: str
    schema_params: type[BaseModel]

    def calcular(
        self, params: BaseModel, empresa_id: str
    ) -> ResultadoPresupuesto: ...


REGISTRY: dict[str, Calculadora] = {}


def registrar(calc: Calculadora) -> Calculadora:
    if calc.accion in REGISTRY:
        raise RuntimeError(f"Calculadora duplicada: {calc.accion}")
    REGISTRY[calc.accion] = calc
    return calc
