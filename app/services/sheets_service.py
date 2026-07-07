import logging
from datetime import datetime, timezone
from typing import Any

from app.config import config

logger = logging.getLogger(__name__)

SHEET_NAME = "Kirim"
HEADERS = [
    "Telegram ID",
    "Telefon raqam",
    "Ism",
    "Mahsulot nomi",
    "Kg miqdori",
    "1 kg narxi",
    "Saqlash muddati (kun)",
    "Umumiy summa",
    "Status",
    "Yaratilgan sana",
]


def product_to_sheet_row(product: dict[str, Any]) -> list[str | int | float]:
    return [
        product.get("telegram_id", ""),
        product.get("phone", ""),
        product.get("client_name", ""),
        product.get("product_name", ""),
        product.get("kg_amount", 0),
        product.get("price_per_kg", 0),
        product.get("storage_days", 0),
        product.get("total_price", 0),
        product.get("status", "active"),
        product.get("created_at", datetime.now(timezone.utc).isoformat()),
    ]


class SheetsService:
    def __init__(self):
        self.sheets_id: str = config.google_sheets_id
        self._client = None
        self._worksheet = None
        self._ready = False

    def is_configured(self) -> bool:
        if not self.sheets_id or self.sheets_id == "your_google_sheet_id_here":
            return False
        import os
        path = config.google_service_account_file
        return bool(os.path.isfile(path))

    async def initialize(self):
        if not self.is_configured():
            logger.info("Google Sheets not configured — skipping")
            return

        try:
            import gspread
            from google.oauth2.service_account import Credentials

            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ]
            creds = Credentials.from_service_account_file(
                config.google_service_account_file, scopes=scopes
            )
            self._client = gspread.authorize(creds)

            try:
                sh = self._client.open_by_key(self.sheets_id)
            except Exception:
                logger.warning("Google Sheet not found by ID: %s", self.sheets_id)
                return

            try:
                self._worksheet = sh.worksheet(SHEET_NAME)
            except gspread.WorksheetNotFound:
                self._worksheet = sh.add_worksheet(title=SHEET_NAME, rows=100, cols=20)

            self._ready = True
            await self._ensure_headers()
            logger.info("Google Sheets ready (sheet: %s)", SHEET_NAME)
        except Exception as e:
            self._ready = False
            logger.warning("Google Sheets init failed: %s", e)

    async def _ensure_headers(self):
        if not self._worksheet:
            return
        existing = self._worksheet.row_values(1)
        if not existing or all(cell == "" for cell in existing):
            self._worksheet.append_row(HEADERS, value_input_option="USER_ENTERED")

    async def append_product_row(self, product: dict[str, Any]) -> bool:
        if not self._ready or not self._worksheet:
            return False
        try:
            row = product_to_sheet_row(product)
            self._worksheet.append_row(row, value_input_option="USER_ENTERED")
            return True
        except Exception as e:
            logger.warning("Sheets append failed: %s", e)
            return False


sheets_service = SheetsService()
