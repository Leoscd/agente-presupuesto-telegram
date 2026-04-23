"""Carga datos de empresa con caché invalidado por mtime de los archivos."""
from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from functools import lru_cache
from pathlib import Path

import pandas as pd

from src.config import settings


class EmpresaNoEncontrada(Exception):
    pass


class MaterialNoEncontrado(Exception):
    pass


@dataclass(frozen=True)
class ConfigEmpresa:
    id: str
    nombre: str
    moneda: str
    activo: bool
    max_edad_precios_dias: int
    cuit: str | None = None
    direccion: str | None = None
    telefono: str | None = None
    email: str | None = None


@dataclass(frozen=True)
class DatosEmpresa:
    config: ConfigEmpresa
    precios_materiales: pd.DataFrame  # cols: codigo, descripcion, unidad, precio, fecha_actualizacion
    precios_mano_obra: pd.DataFrame   # cols: tarea, descripcion, unidad, precio, equipo_minimo
    rendimientos: dict[str, Decimal]  # codigo -> coef. desperdicio (>=1.0)
    materiales_disponibles: list[str]

    def ruta(self) -> Path:
        return settings.data_dir / self.config.id


def _empresa_dir(empresa_id: str) -> Path:
    d = settings.data_dir / empresa_id
    if not d.is_dir():
        raise EmpresaNoEncontrada(empresa_id)
    return d


def _mtime_signature(empresa_id: str) -> tuple[float, ...]:
    d = _empresa_dir(empresa_id)
    archivos = [
        "config.json",
        "precios_materiales.csv",
        "precios_mano_obra.csv",
        "rendimientos.csv",
        "materiales_disponibles.json",
    ]
    return tuple((d / a).stat().st_mtime if (d / a).exists() else 0.0 for a in archivos)


@lru_cache(maxsize=64)
def _cargar(empresa_id: str, _sig: tuple[float, ...]) -> DatosEmpresa:
    del _sig  # solo para invalidar caché
    d = _empresa_dir(empresa_id)

    cfg_raw = json.loads((d / "config.json").read_text(encoding="utf-8"))
    config = ConfigEmpresa(
        id=empresa_id,
        nombre=cfg_raw["nombre"],
        moneda=cfg_raw.get("moneda", "ARS"),
        activo=cfg_raw.get("activo", True),
        max_edad_precios_dias=cfg_raw.get("max_edad_precios_dias", 30),
        cuit=cfg_raw.get("cuit"),
        direccion=cfg_raw.get("direccion"),
        telefono=cfg_raw.get("telefono"),
        email=cfg_raw.get("email"),
    )

    mat = pd.read_csv(
        d / "precios_materiales.csv",
        dtype={"codigo": str, "descripcion": str, "unidad": str},
    )
    mat["precio"] = mat["precio"].map(lambda v: Decimal(str(v)))
    mat["fecha_actualizacion"] = pd.to_datetime(mat["fecha_actualizacion"]).dt.date

    mo = pd.read_csv(
        d / "precios_mano_obra.csv",
        dtype={"tarea": str, "descripcion": str, "unidad": str},
    )
    mo["precio"] = mo["precio"].map(lambda v: Decimal(str(v)))

    rend_path = d / "rendimientos.csv"
    if rend_path.exists():
        rdf = pd.read_csv(rend_path, dtype={"codigo": str})
        rendimientos = {
            str(r["codigo"]): Decimal(str(r["coeficiente"])) for _, r in rdf.iterrows()
        }
    else:
        rendimientos = {}

    disponibles = json.loads((d / "materiales_disponibles.json").read_text(encoding="utf-8"))

    return DatosEmpresa(
        config=config,
        precios_materiales=mat,
        precios_mano_obra=mo,
        rendimientos=rendimientos,
        materiales_disponibles=list(disponibles),
    )


def cargar_empresa(empresa_id: str) -> DatosEmpresa:
    """API pública. Hot-reload: cualquier edición del CSV invalida la caché."""
    return _cargar(empresa_id, _mtime_signature(empresa_id))


def precio_material(datos: DatosEmpresa, codigo: str) -> Decimal:
    fila = datos.precios_materiales.loc[datos.precios_materiales["codigo"] == codigo]
    if fila.empty:
        raise MaterialNoEncontrado(f"Material {codigo} no tiene precio en {datos.config.id}")
    return Decimal(fila.iloc[0]["precio"])


def precio_mano_obra(datos: DatosEmpresa, tarea: str) -> Decimal:
    fila = datos.precios_mano_obra.loc[datos.precios_mano_obra["tarea"] == tarea]
    if fila.empty:
        raise MaterialNoEncontrado(f"Tarea {tarea} no tiene precio en {datos.config.id}")
    return Decimal(fila.iloc[0]["precio"])


def rendimiento(datos: DatosEmpresa, codigo: str, default: Decimal = Decimal("1.0")) -> Decimal:
    return datos.rendimientos.get(codigo, default)
