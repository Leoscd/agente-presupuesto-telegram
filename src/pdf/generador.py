"""Renderiza ResultadoPresupuesto a PDF usando Jinja2 + WeasyPrint.

Template default: src/pdf/templates/default/
Custom por empresa: empresas/{id}/pdf_template/
"""
from __future__ import annotations

import re
import secrets
from datetime import date
from decimal import Decimal
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

# WeasyPrint requiere GTK en Windows. Import lazy: solo falla si se genera un PDF.
try:
    from weasyprint import HTML as _WeasyHTML
    _WEASY_OK = True
except OSError:
    _WeasyHTML = None  # type: ignore[assignment,misc]
    _WEASY_OK = False

from src.config import settings
from src.datos.loader import DatosEmpresa
from src.rubros.base import ResultadoPresupuesto

TEMPLATE_NAME = "presupuesto.html.j2"
DEFAULT_TEMPLATE_DIR = Path(__file__).parent / "templates" / "default"


def _slug(texto: str) -> str:
    s = re.sub(r"[^\w\s-]", "", texto, flags=re.UNICODE).strip().lower()
    return re.sub(r"[\s_-]+", "_", s)[:40] or "estudio"


def _formato_moneda(valor: Decimal | float, moneda: str = "ARS") -> str:
    """Formato argentino: 1.234.567,89"""
    del moneda
    v = Decimal(str(valor)).quantize(Decimal("0.01"))
    signo = "-" if v < 0 else ""
    entero, _, dec = f"{abs(v):.2f}".partition(".")
    partes = []
    while len(entero) > 3:
        partes.insert(0, entero[-3:])
        entero = entero[:-3]
    partes.insert(0, entero)
    entero_fmt = ".".join(partes)
    return f"{signo}$ {entero_fmt},{dec}"


def _template_dir(empresa_id: str) -> Path:
    custom = settings.data_dir / empresa_id / "pdf_template"
    if custom.is_dir() and (custom / TEMPLATE_NAME).exists():
        return custom
    return DEFAULT_TEMPLATE_DIR


def _build_env(dir_: Path) -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(dir_)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["moneda"] = _formato_moneda
    return env


def generar_pdf(
    resultado: ResultadoPresupuesto,
    datos_empresa: DatosEmpresa,
    destino_dir: Path,
    cliente: str | None = None,
) -> Path:
    destino_dir.mkdir(parents=True, exist_ok=True)

    tpl_dir = _template_dir(datos_empresa.config.id)
    env = _build_env(tpl_dir)
    template = env.get_template(TEMPLATE_NAME)

    id_corto = secrets.token_hex(3)
    fecha = date.today().isoformat()
    contexto = {
        "empresa": datos_empresa.config,
        "resultado": resultado,
        "fecha": fecha,
        "id_corto": id_corto,
        "cliente": cliente or "—",
        "metadata": {},  # reservado para flags de template (borrador, etc.)
    }
    html = template.render(**contexto)

    slug = _slug(datos_empresa.config.nombre)
    out = destino_dir / f"Presupuesto_{slug}_{fecha}_{id_corto}.pdf"

    if not _WEASY_OK:
        raise RuntimeError(
            "WeasyPrint no pudo cargar GTK. "
            "Instalá el runtime desde https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer "
            "y reiniciá el bot para habilitar la generación de PDFs."
        )
    _WeasyHTML(string=html, base_url=str(tpl_dir)).write_pdf(str(out))
    return out
