import logging
from datetime import datetime, timezone
from typing import Any

from app.config import config

logger = logging.getLogger(__name__)

KIRIM_SHEET_NAME = "Kirim"
CHIQIM_SHEET_NAME = "Chiqim"

KIRIM_HEADERS = [
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

CHIQIM_HEADERS = [
    "Product ID",
    "Telegram ID",
    "Telefon raqam",
    "Ism",
    "Mahsulot nomi",
    "Kg miqdori",
    "1 kg narxi",
    "Saqlash muddati (kun)",
    "Umumiy summa",
    "Chiqim sanasi",
    "Admin Telegram ID",
    "Izoh",
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


def exit_to_sheet_row(exit_data: dict[str, Any]) -> list[str | int | float]:
    return [
        exit_data.get("product_id", ""),
        exit_data.get("telegram_id", ""),
        exit_data.get("phone", ""),
        exit_data.get("client_name", ""),
        exit_data.get("product_name", ""),
        exit_data.get("kg_amount", 0),
        exit_data.get("price_per_kg", 0),
        exit_data.get("storage_days", 0),
        exit_data.get("total_price", 0),
        exit_data.get("exited_at", datetime.now(timezone.utc).isoformat()),
        exit_data.get("created_by_admin_id", ""),
        exit_data.get("note", "") or "",
    ]


class SheetsService:
    def __init__(self):
        self.sheets_id: str = config.google_sheets_id
        self._client = None
        self._kirim_worksheet = None
        self._chiqim_worksheet = None
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

            for name, attr in [(KIRIM_SHEET_NAME, "_kirim_worksheet"),
                               (CHIQIM_SHEET_NAME, "_chiqim_worksheet")]:
                try:
                    ws = sh.worksheet(name)
                except gspread.WorksheetNotFound:
                    ws = sh.add_worksheet(title=name, rows=100, cols=20)
                setattr(self, attr, ws)

            self._ready = True
            await self._ensure_headers()
            logger.info("Google Sheets ready (sheets: %s, %s)",
                        KIRIM_SHEET_NAME, CHIQIM_SHEET_NAME)
        except Exception as e:
            self._ready = False
            logger.warning("Google Sheets init failed: %s", e)

    async def _ensure_headers(self):
        for ws, headers in [(self._kirim_worksheet, KIRIM_HEADERS),
                            (self._chiqim_worksheet, CHIQIM_HEADERS)]:
            if not ws:
                continue
            existing = ws.row_values(1)
            if not existing or all(cell == "" for cell in existing):
                ws.append_row(headers, value_input_option="USER_ENTERED")

    async def append_product_row(self, product: dict[str, Any]) -> bool:
        if not self._ready or not self._kirim_worksheet:
            return False
        try:
            row = product_to_sheet_row(product)
            self._kirim_worksheet.append_row(row, value_input_option="USER_ENTERED")
            return True
        except Exception as e:
            logger.warning("Sheets append (Kirim) failed: %s", e)
            return False

    async def append_exit_row(self, exit_data: dict[str, Any]) -> bool:
        if not self._ready or not self._chiqim_worksheet:
            return False
        try:
            row = exit_to_sheet_row(exit_data)
            self._chiqim_worksheet.append_row(row, value_input_option="USER_ENTERED")
            return True
        except Exception as e:
            logger.warning("Sheets append (Chiqim) failed: %s", e)
            return False


sheets_service = SheetsService()
