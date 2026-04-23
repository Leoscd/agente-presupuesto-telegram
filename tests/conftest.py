"""Inicializa env vars dummy para que src.config no falle al importar en tests."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.environ.setdefault("TELEGRAM_TOKEN", "test-token")
os.environ.setdefault("MINIMAX_API_KEY", "test-key")
os.environ.setdefault("DATA_DIR", str(ROOT / "empresas"))
os.environ.setdefault("DB_PATH", str(ROOT / "data" / "test.sqlite"))
