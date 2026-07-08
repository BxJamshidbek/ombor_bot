import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any

import requests

from app.config import config

logger = logging.getLogger(__name__)

MAIN_SHEET_NAME = "Ombor"
PAYMENT_HISTORY_SHEET_NAME = "To'lovlar tarixi"

MAIN_HEADERS = [
    "Product ID",
    "Telegram ID",
    "Telefon raqam",
    "Ism",
    "Mahsulot nomi",
    "Kg miqdori",
    "Qutilar soni",
    "1 kg narxi",
    "Umumiy summa",
    "To'langan summa",
    "Qolgan summa",
    "Status",
    "Yaratilgan sana",
    "Chiqim sanasi",
    "Izoh",
]

PAYMENT_HISTORY_HEADERS = [
    "Payment ID",
    "Telegram ID",
    "Telefon raqam",
    "Ism",
    "To'lov summasi",
    "Izoh",
    "Admin Telegram ID",
    "Yaratilgan sana",
]


def product_to_main_sheet_row(
    product: dict[str, Any],
    paid_amount: float = 0,
    remaining_amount: float | None = None,
) -> list[str | int | float]:
    total = product.get("total_price", 0)
    return [
        product.get("id", ""),
        product.get("telegram_id", ""),
        product.get("phone", ""),
        product.get("client_name", ""),
        product.get("product_name", ""),
        product.get("kg_amount", 0),
        product.get("box_count", 0),
        product.get("price_per_kg", 0),
        total,
        paid_amount,
        remaining_amount if remaining_amount is not None else total,
        product.get("status", "active"),
        product.get("created_at") or "",
        "",
        "",
    ]


def payment_to_history_row(payment: dict[str, Any]) -> list[str | int | float]:
    return [
        payment.get("id", ""),
        payment.get("telegram_id", ""),
        payment.get("phone", ""),
        payment.get("client_name", ""),
        payment.get("amount", 0),
        payment.get("note", "") or "",
        payment.get("created_by_admin_id", ""),
        payment.get("created_at", datetime.now(timezone.utc).isoformat()),
    ]


def payment_updates_to_payload(
    allocation: dict[int, dict],
) -> list[dict]:
    updates = []
    for pid, alloc in allocation.items():
        updates.append({
            "product_id": pid,
            "paid_amount": alloc["paid_amount"],
            "remaining_amount": alloc["remaining_amount"],
        })
    return updates


class SheetsService:
    def __init__(self):
        self.sheets_id: str = config.google_sheets_id
        self._client = None
        self._main_worksheet = None
        self._payment_worksheet = None
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
                resp = await asyncio.to_thread(requests.get, webapp_url, timeout=5)
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

            for name, attr in [(MAIN_SHEET_NAME, "_main_worksheet"),
                               (PAYMENT_HISTORY_SHEET_NAME, "_payment_worksheet")]:
                try:
                    ws = sh.worksheet(name)
                except gspread.WorksheetNotFound:
                    ws = sh.add_worksheet(title=name, rows=100, cols=20)
                setattr(self, attr, ws)

            self._ready = True
            await self._ensure_headers()
            logger.info("Google Sheets ready (sheets: %s, %s)",
                        MAIN_SHEET_NAME, PAYMENT_HISTORY_SHEET_NAME)
        except Exception as e:
            self._ready = False
            logger.warning("Google Sheets init failed: %s", e)

    async def _ensure_headers(self):
        for ws, headers in [(self._main_worksheet, MAIN_HEADERS),
                            (self._payment_worksheet, PAYMENT_HISTORY_HEADERS)]:
            if not ws:
                continue
            existing = ws.row_values(1)
            if not existing or all(cell == "" for cell in existing):
                ws.append_row(headers, value_input_option="USER_ENTERED")

    async def _append_via_script(self, action: str, row: list) -> bool:
        if not self._ready:
            logger.warning("Append via script skipped: not ready")
            return False
        webapp_url = config.google_script_webapp_url.rstrip("/")
        payload = {
            "secret": config.google_script_secret,
            "action": action,
            "data": row,
        }
        logger.info("Apps Script POST: action=%s", action)
        try:
            resp = await asyncio.to_thread(
                requests.post, webapp_url, json=payload, timeout=5
            )
            logger.info("Apps Script response: status=%s", resp.status_code)
            if resp.status_code != 200:
                logger.warning("Apps Script HTTP %s: %s", resp.status_code, resp.text[:200])
                return False
            try:
                result = resp.json()
            except ValueError:
                logger.warning("Apps Script non-JSON: %s", resp.text[:300])
                return False
            logger.info("Apps Script result: %s", result)
            if result.get("ok"):
                return True
            logger.warning("Apps Script failed: %s", result)
            return False
        except Exception as e:
            logger.exception("Apps Script request error: %s", e)
            return False

    async def _update_via_script(self, action: str, data: dict) -> bool:
        if not self._ready:
            return False
        webapp_url = config.google_script_webapp_url.rstrip("/")
        payload = {
            "secret": config.google_script_secret,
            "action": action,
            "data": data,
        }
        logger.info("Apps Script POST: action=%s", action)
        try:
            resp = await asyncio.to_thread(
                requests.post, webapp_url, json=payload, timeout=5
            )
            logger.info("Apps Script response: status=%s", resp.status_code)
            if resp.status_code != 200:
                logger.warning("Apps Script HTTP %s: %s", resp.status_code, resp.text[:200])
                return False
            try:
                result = resp.json()
            except ValueError:
                logger.warning("Apps Script non-JSON: %s", resp.text[:300])
                return False
            if result.get("ok"):
                return True
            logger.warning("Apps Script failed: %s", result)
            return False
        except Exception as e:
            logger.exception("Apps Script request error: %s", e)
            return False

    async def append_product_row(self, product: dict[str, Any]) -> bool:
        if self._script_mode:
            row = product_to_main_sheet_row(product)
            return await self._append_via_script("append_product", row)
        if not self._ready or not self._main_worksheet:
            return False
        try:
            row = product_to_main_sheet_row(product)
            self._main_worksheet.append_row(row, value_input_option="USER_ENTERED")
            return True
        except Exception as e:
            logger.warning("Sheets append product failed: %s", e)
            return False

    async def update_exit_row(self, exit_data: dict[str, Any]) -> bool:
        exit_data["status"] = "exited"
        row_data = {**exit_data, "id": exit_data.get("product_id")}
        row = product_to_main_sheet_row(
            row_data,
            paid_amount=0,
            remaining_amount=exit_data.get("total_price", 0),
        )
        data = {
            "product_id": exit_data.get("product_id"),
            "status": "exited",
            "exited_at": exit_data.get("exited_at", ""),
            "note": exit_data.get("note", "") or "",
            "row": row,
        }
        if self._script_mode:
            return await self._update_via_script("update_exit", data)
        if not self._ready or not self._main_worksheet:
            return False
        try:
            product_id = str(data["product_id"])
            cell = self._main_worksheet.find(product_id, in_column=1)
            if cell:
                self._main_worksheet.update_cell(cell.row, 12, "exited")
                self._main_worksheet.update_cell(cell.row, 14, data["exited_at"])
                self._main_worksheet.update_cell(cell.row, 15, data["note"])
                return True
            self._main_worksheet.append_row(row, value_input_option="USER_ENTERED")
            return True
        except Exception as e:
            logger.warning("Sheets update exit failed: %s", e)
            return False

    async def append_payment_history(self, payment: dict[str, Any]) -> bool:
        if self._script_mode:
            row = payment_to_history_row(payment)
            return await self._append_via_script("append_payment_history", row)
        if not self._ready or not self._payment_worksheet:
            return False
        try:
            row = payment_to_history_row(payment)
            self._payment_worksheet.append_row(row, value_input_option="USER_ENTERED")
            return True
        except Exception as e:
            logger.warning("Sheets append payment failed: %s", e)
            return False

    async def update_payment_rows(self, updates: list[dict]) -> bool:
        if self._script_mode:
            return await self._update_via_script("update_payments", updates)
        if not self._ready or not self._main_worksheet:
            return False
        try:
            for u in updates:
                pid = str(u["product_id"])
                cell = self._main_worksheet.find(pid, in_column=1)
                if cell:
                    self._main_worksheet.update_cell(cell.row, 10, u["paid_amount"])
                    self._main_worksheet.update_cell(cell.row, 11, u["remaining_amount"])
            return True
        except Exception as e:
            logger.warning("Sheets update payments failed: %s", e)
            return False


sheets_service = SheetsService()
