"""Valida y guarda un template PDF custom subido por el arquitecto (zip)."""
from __future__ import annotations

import re
import shutil
import tempfile
import zipfile
from pathlib import Path

from src.config import settings

UNSAFE_PATTERNS = [
    re.compile(r"<\s*script", re.IGNORECASE),
    re.compile(r"\son\w+\s*=", re.IGNORECASE),     # onclick=, onload=, etc.
    re.compile(r"(?:https?:)?//[a-z0-9.\-]", re.IGNORECASE),  # URLs externas
    re.compile(r"\{\%\s*import\s+", re.IGNORECASE),
    re.compile(r"\{\%\s*include\s+['\"][/\\]", re.IGNORECASE),  # includes absolutos
]
MAX_ZIP_BYTES = 5 * 1024 * 1024
MAX_FILES = 50
ALLOWED_EXT = {".html", ".j2", ".css", ".png", ".jpg", ".jpeg", ".svg", ".ttf", ".woff", ".woff2"}


class TemplateInvalido(Exception):
    pass


def _escanear(texto: str) -> list[str]:
    return [p.pattern for p in UNSAFE_PATTERNS if p.search(texto)]


def instalar_template(empresa_id: str, zip_path: Path) -> Path:
    if zip_path.stat().st_size > MAX_ZIP_BYTES:
        raise TemplateInvalido(f"ZIP demasiado grande (max {MAX_ZIP_BYTES // 1024} KB)")

    destino = settings.data_dir / empresa_id / "pdf_template"
    destino.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        with zipfile.ZipFile(zip_path) as zf:
            infos = zf.infolist()
            if len(infos) > MAX_FILES:
                raise TemplateInvalido(f"Demasiados archivos (max {MAX_FILES})")
            for info in infos:
                # Path traversal
                if info.filename.startswith(("/", "\\")) or ".." in Path(info.filename).parts:
                    raise TemplateInvalido(f"Path inseguro: {info.filename}")
                ext = Path(info.filename).suffix.lower()
                if info.is_dir():
                    continue
                if ext not in ALLOWED_EXT:
                    raise TemplateInvalido(f"Extensión no permitida: {info.filename}")
            zf.extractall(tmp_path)

        # Validar contenido de HTML/CSS/J2
        for p in tmp_path.rglob("*"):
            if p.is_file() and p.suffix.lower() in {".html", ".j2", ".css"}:
                txt = p.read_text(encoding="utf-8", errors="replace")
                hits = _escanear(txt)
                if hits:
                    raise TemplateInvalido(
                        f"{p.name}: patrones inseguros detectados: {hits}"
                    )

        entry = tmp_path / "presupuesto.html.j2"
        if not entry.exists():
            raise TemplateInvalido("falta presupuesto.html.j2 en la raíz del zip")

        if destino.exists():
            shutil.rmtree(destino)
        shutil.copytree(tmp_path, destino)

    return destino
