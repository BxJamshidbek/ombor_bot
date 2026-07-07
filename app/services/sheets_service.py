"""
Google Sheets integratsiyasi.

Hozircha skeleton — faqatgina config yuklanadi va
gspread client tayyorlanadi, real ishlatilmaydi.
"""

from app.config import config


class SheetsService:
    def __init__(self):
        self.sheets_id: str = config.google_sheets_id
        self._client = None

    async def initialize(self):
        if not self.sheets_id:
            return

        # Google Sheets ga ulanish keyingi bosqichda to'liq yoziladi
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

    async def get_sheet(self, sheet_name: str = "Sheet1"):
        if self._client is None:
            return None
        sh = self._client.open_by_key(self.sheets_id)
        return sh.worksheet(sheet_name)


sheets_service = SheetsService()
