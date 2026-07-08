import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    bot_token: str = field(default_factory=lambda: os.getenv("BOT_TOKEN", ""))
    admin_ids: list[int] = field(default_factory=list)
    database_url: str = field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL", "sqlite+aiosqlite:///data/ombor_bot.sqlite3"
        )
    )
    google_sheets_id: str = field(
        default_factory=lambda: os.getenv("GOOGLE_SHEETS_ID", "")
    )
    google_service_account_file: str = field(
        default_factory=lambda: os.getenv(
            "GOOGLE_SERVICE_ACCOUNT_FILE", "credentials/service_account.json"
        )
    )
    google_script_webapp_url: str = field(
        default_factory=lambda: os.getenv("GOOGLE_SCRIPT_WEBAPP_URL", "")
    )
    google_script_secret: str = field(
        default_factory=lambda: os.getenv("GOOGLE_SCRIPT_SECRET", "")
    )
    bot_mode: str = field(
        default_factory=lambda: os.getenv("BOT_MODE", "polling")
    )
    webhook_base_url: str = field(
        default_factory=lambda: os.getenv("WEBHOOK_BASE_URL", "")
    )
    webhook_secret_path: str = field(
        default_factory=lambda: os.getenv("WEBHOOK_SECRET_PATH", "")
    )
    webapp_host: str = field(
        default_factory=lambda: os.getenv("WEBAPP_HOST", "127.0.0.1")
    )
    webapp_port: int = field(
        default_factory=lambda: int(os.getenv("WEBAPP_PORT", "8080"))
    )

    def __post_init__(self):
        raw_admin_ids = os.getenv("ADMIN_IDS", "")
        if raw_admin_ids:
            self.admin_ids = [
                int(x.strip()) for x in raw_admin_ids.split(",") if x.strip().isdigit()
            ]

        if not self.bot_token:
            raise ValueError(
                "BOT_TOKEN environment variable is not set. "
                "Create a .env file based on .env.example"
            )

        if self.bot_mode == "webhook":
            if not self.webhook_base_url:
                raise ValueError(
                    "WEBHOOK_BASE_URL is required when BOT_MODE=webhook"
                )
            if not self.webhook_secret_path:
                raise ValueError(
                    "WEBHOOK_SECRET_PATH is required when BOT_MODE=webhook"
                )


config = Config()
