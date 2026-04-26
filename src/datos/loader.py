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


def actualizar_precio_material(empresa_id: str, codigo: str, nuevo_precio: Decimal) -> Decimal:
    """Edita precio en precios_materiales.csv. Devuelve precio anterior.
    El hot-reload es automático: mtime cambia → proxima llamada a cargar_empresa() recarga.
    """
    from datetime import date
    d = _empresa_dir(empresa_id)
    path = d / "precios_materiales.csv"
    df = pd.read_csv(path, dtype={"codigo": str, "descripcion": str, "unidad": str})
    codigo_upper = codigo.upper()
    mask = df["codigo"] == codigo_upper
    if not mask.any():
        # intento case-insensitive sobre descripcion
        mask = df["descripcion"].str.upper() == codigo.upper()
        if not mask.any():
            raise MaterialNoEncontrado(f"Codigo '{codigo}' no encontrado en materiales de {empresa_id}")
    precio_anterior = Decimal(str(df.loc[mask, "precio"].iloc[0]))
    df.loc[mask, "precio"] = float(nuevo_precio)
    df.loc[mask, "fecha_actualizacion"] = date.today().isoformat()
    df.to_csv(path, index=False)
    return precio_anterior


def actualizar_precio_mano_obra(empresa_id: str, tarea: str, nuevo_precio: Decimal) -> Decimal:
    """Edita precio en precios_mano_obra.csv. Devuelve precio anterior."""
    from datetime import date
    d = _empresa_dir(empresa_id)
    path = d / "precios_mano_obra.csv"
    df = pd.read_csv(path, dtype={"tarea": str, "descripcion": str, "unidad": str})
    tarea_upper = tarea.upper()
    mask = df["tarea"] == tarea_upper
    if not mask.any():
        mask = df["descripcion"].str.upper().str.contains(tarea.upper(), na=False)
        if not mask.any():
            raise MaterialNoEncontrado(f"Tarea '{tarea}' no encontrada en MO de {empresa_id}")
    precio_anterior = Decimal(str(df.loc[mask, "precio"].iloc[0]))
    df.loc[mask, "precio"] = float(nuevo_precio)
    df.to_csv(path, index=False)
    return precio_anterior


def listar_materiales_con_descripcion(empresa_id: str) -> list[dict]:
    """Devuelve lista [{codigo, descripcion, unidad, precio}] para pasar a MiniMax."""
    datos = cargar_empresa(empresa_id)
    return [
        {
            "codigo": str(r["codigo"]),
            "descripcion": str(r["descripcion"]),
            "unidad": str(r["unidad"]),
            "precio_actual": float(r["precio"]),
        }
        for _, r in datos.precios_materiales.iterrows()
    ]


def listar_mo_con_descripcion(empresa_id: str) -> list[dict]:
    """Devuelve lista [{tarea, descripcion, unidad, precio}] para pasar a MiniMax."""
    datos = cargar_empresa(empresa_id)
    return [
        {
            "tarea": str(r["tarea"]),
            "descripcion": str(r["descripcion"]),
            "unidad": str(r["unidad"]),
            "precio_actual": float(r["precio"]),
        }
        for _, r in datos.precios_mano_obra.iterrows()
    ]
