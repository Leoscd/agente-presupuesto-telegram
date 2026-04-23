"""Entrypoint del bot. Polling en dev, webhook en prod."""
from __future__ import annotations

import logging

from telegram.ext import Application, ApplicationBuilder

from src.bot import handlers
from src.config import settings
from src.persistencia import db


def _setup_logging() -> None:
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def main() -> None:
    _setup_logging()
    db.init_db()

    app: Application = ApplicationBuilder().token(settings.telegram_token).build()
    handlers.registrar(app)

    if settings.env == "prod" and settings.webhook_url:
        app.run_webhook(
            listen="0.0.0.0",
            port=settings.webhook_port,
            url_path=settings.webhook_secret or "",
            webhook_url=f"{settings.webhook_url.rstrip('/')}/{settings.webhook_secret or ''}",
            secret_token=settings.webhook_secret,
        )
    else:
        app.run_polling(allowed_updates=None)


if __name__ == "__main__":
    main()
