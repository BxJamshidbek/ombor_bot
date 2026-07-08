import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import requests

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
    "Tugash sanasi",
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


def calculate_expire_date(created_at: str, storage_days: int) -> str:
    if not created_at or not isinstance(storage_days, int):
        return ""
    try:
        if "+" in created_at or created_at.endswith("Z"):
            dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        else:
            dt = datetime.fromisoformat(created_at)
        expire = dt + timedelta(days=storage_days)
        return expire.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return ""


def product_to_sheet_row(product: dict[str, Any]) -> list[str | int | float]:
    created_at = product.get("created_at", datetime.now(timezone.utc).isoformat())
    storage_days = product.get("storage_days", 0)
    return [
        product.get("telegram_id", ""),
        product.get("phone", ""),
        product.get("client_name", ""),
        product.get("product_name", ""),
        product.get("kg_amount", 0),
        product.get("price_per_kg", 0),
        storage_days,
        calculate_expire_date(created_at, storage_days),
        product.get("total_price", 0),
        product.get("status", "active"),
        created_at,
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
        self._script_mode = False

    def is_configured(self) -> bool:
        if config.google_script_webapp_url and config.google_script_secret:
            return True
        if not self.sheets_id or self.sheets_id == "your_google_sheet_id_here":
            return False
        import os
        path = config.google_service_account_file
        return bool(os.path.isfile(path))

    async def initialize(self):
        if config.google_script_webapp_url and config.google_script_secret:
            self._script_mode = True
            self._ready = True
            webapp_url = config.google_script_webapp_url.rstrip("/")
            try:
                resp = await asyncio.to_thread(requests.get, webapp_url, timeout=15)
                if resp.status_code == 200 and resp.json().get("ok"):
                    logger.info("Google Sheets (Apps Script) ready at %s", webapp_url)
                else:
                    logger.warning("Apps Script health check failed: status=%s body=%s",
                                   resp.status_code, resp.text[:200])
            except Exception as e:
                logger.warning("Apps Script health check error: %s", e)
            return

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

    async def _append_via_script(self, action: str, row: list) -> bool:
        if not self._ready:
            return False
        webapp_url = config.google_script_webapp_url.rstrip("/")
        payload = {
            "secret": config.google_script_secret,
            "action": action,
            "data": row,
        }
        try:
            resp = await asyncio.to_thread(
                requests.post, webapp_url, json=payload, timeout=15
            )
            if resp.status_code != 200:
                logger.warning("Apps Script HTTP %s: %s", resp.status_code, resp.text[:200])
                return False
            try:
                result = resp.json()
            except ValueError:
                logger.warning("Apps Script non-JSON response: %s", resp.text[:300])
                return False
            if result.get("ok"):
                return True
            logger.warning("Apps Script append failed: %s", result)
            return False
        except Exception as e:
            logger.warning("Apps Script request error: %s", e)
            return False

    async def append_product_row(self, product: dict[str, Any]) -> bool:
        if self._script_mode:
            row = product_to_sheet_row(product)
            return await self._append_via_script("append_kirim", row)
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
        if self._script_mode:
            row = exit_to_sheet_row(exit_data)
            return await self._append_via_script("append_chiqim", row)
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
