from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    telegram_token: str = Field(..., alias="TELEGRAM_TOKEN")

    minimax_api_key: str = Field(..., alias="MINIMAX_API_KEY")
    minimax_base_url: str = Field("https://api.minimax.io/v1", alias="MINIMAX_BASE_URL")
    minimax_model: str = Field("MiniMax-M2", alias="MINIMAX_MODEL")
    minimax_vision_model: str = Field("MiniMax-M2.1", alias="MINIMAX_VISION_MODEL")

    env: Literal["dev", "prod"] = Field("dev", alias="ENV")
    log_level: str = Field("INFO", alias="LOG_LEVEL")

    data_dir: Path = Field(ROOT / "empresas", alias="DATA_DIR")
    db_path: Path = Field(ROOT / "data" / "app.sqlite", alias="DB_PATH")

    admin_telegram_chat_id: int | None = Field(None, alias="ADMIN_TELEGRAM_CHAT_ID")

    webhook_url: str | None = Field(None, alias="WEBHOOK_URL")
    webhook_port: int = Field(8443, alias="WEBHOOK_PORT")
    webhook_secret: str | None = Field(None, alias="WEBHOOK_SECRET")

    minimax_budget_usd: float = Field(10.0, alias="MINIMAX_BUDGET_USD")
    minimax_alert_threshold: float = Field(0.8, alias="MINIMAX_ALERT_THRESHOLD")


settings = Settings()  # type: ignore[call-arg]
