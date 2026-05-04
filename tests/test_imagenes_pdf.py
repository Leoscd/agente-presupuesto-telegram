"""Tests para imágenes en PDF (Tarea 17)."""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from decimal import Decimal

from src.pdf import generador
from src.rubros.base import ResultadoPresupuesto, Partida


def _resultado_dummy() -> ResultadoPresupuesto:
    return ResultadoPresupuesto(
        rubro="revoque_fino",
        partidas=[
            Partida(
                descripcion="Revoque",
                unidad="m2",
                cantidad=Decimal("45"),
                precio_unitario=Decimal("1000"),
                subtotal=Decimal("45000"),
                codigo="REVOQUE_FINO",
                categoria="material",
            )
        ],
        total=Decimal("45000"),
        subtotal_materiales=Decimal("45000"),
        subtotal_mano_obra=Decimal("0"),
        advertencias=[],
    )


def test_generar_pdf_sin_imagenes(tmp_path):
    """generar_pdf acepta imagenes=None sin error."""
    from src.datos.loader import DatosEmpresa, ConfigEmpresa

    datos = MagicMock(spec=DatosEmpresa)
    datos.config.id = "_plantilla"
    datos.config.nombre = "Test"

    # No generar PDF real (WeasyPrint puede no estar disponible)
    with patch("src.pdf.generador._WEASY_OK", False):
        with pytest.raises(RuntimeError, match="WeasyPrint"):
            generador.generar_pdf(_resultado_dummy(), datos, tmp_path, imagenes=None)


def test_generar_pdf_con_imagenes_vacia(tmp_path):
    """generar_pdf acepta lista vacía [] sin error."""
    from src.datos.loader import DatosEmpresa

    datos = MagicMock(spec=DatosEmpresa)
    datos.config.id = "_plantilla"
    datos.config.nombre = "Test"

    with patch("src.pdf.generador._WEASY_OK", False):
        with pytest.raises(RuntimeError, match="WeasyPrint"):
            generador.generar_pdf(_resultado_dummy(), datos, tmp_path, imagenes=[])


def test_contexto_incluye_imagenes(tmp_path):
    """El contexto de Jinja incluye la lista de imágenes existentes."""
    img1 = tmp_path / "foto1.jpg"
    img1.write_bytes(b"fake-image")
    img_no_existe = tmp_path / "inexistente.jpg"

    capturado = {}

    original_render = None

    tpl = MagicMock()
    tpl.render = lambda **ctx: capturado.update(ctx) or "<html></html>"

    from src.datos.loader import DatosEmpresa

    datos = MagicMock(spec=DatosEmpresa)
    datos.config.id = "_plantilla"
    datos.config.nombre = "Test"

    with patch("src.pdf.generador._build_env", return_value=MagicMock(get_template=MagicMock(return_value=tpl))):
        with patch("src.pdf.generador._WEASY_OK", False):
            try:
                generador.generar_pdf(
                    _resultado_dummy(),
                    datos,
                    tmp_path,
                    imagenes=[img1, img_no_existe],
                )
            except RuntimeError:
                pass

    # Solo img1 existe → solo img1 en el contexto
    assert str(img1) in capturado.get("imagenes", [])
    assert str(img_no_existe) not in capturado.get("imagenes", [])


def test_imagenes_path_none_se_ignora(tmp_path):
    """None en imagenes se ignora, no incluye strings None."""
    from src.datos.loader import DatosEmpresa

    datos = MagicMock(spec=DatosEmpresa)
    datos.config.id = "_plantilla"
    datos.config.nombre = "Test"

    capturado = {}
    tpl = MagicMock()
    tpl.render = lambda **ctx: capturado.update(ctx) or "<html></html>"

    with patch("src.pdf.generador._build_env", return_value=MagicMock(get_template=MagicMock(return_value=tpl))):
        with patch("src.pdf.generador._WEASY_OK", False):
            try:
                generador.generar_pdf(_resultado_dummy(), datos, tmp_path, imagenes=None)
            except RuntimeError:
                pass

    assert "imagenes" in capturado
    assert None not in capturado["imagenes"]