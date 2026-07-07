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


config = Config()
