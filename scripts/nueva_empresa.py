"""CLI: crea una empresa nueva copiando _plantilla.

Uso:
    python -m scripts.nueva_empresa "Estudio Ramos"
    python -m scripts.nueva_empresa "Estudio Ramos" --id estudio_ramos
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLANTILLA = ROOT / "empresas" / "_plantilla"


def _slug(texto: str) -> str:
    s = re.sub(r"[^\w\s-]", "", texto, flags=re.UNICODE).strip().lower()
    return re.sub(r"[\s_-]+", "_", s) or "empresa"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("nombre", help='Nombre visible del estudio, ej: "Estudio Ramos"')
    parser.add_argument("--id", default=None, help="ID de carpeta (default: slug del nombre)")
    parser.add_argument("--force", action="store_true", help="Sobreescribir si existe")
    args = parser.parse_args()

    empresa_id = args.id or _slug(args.nombre)
    destino = ROOT / "empresas" / empresa_id

    if destino.exists():
        if not args.force:
            print(f"Ya existe {destino}. Usá --force para sobreescribir.", file=sys.stderr)
            return 1
        shutil.rmtree(destino)

    shutil.copytree(PLANTILLA, destino)

    cfg_path = destino / "config.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    cfg["nombre"] = args.nombre
    cfg_path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"✅ Empresa '{args.nombre}' creada en {destino}")
    print("Editá los CSVs con tus precios reales y materiales_disponibles.json.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
