/**
 * Ombor Bot — Google Sheets Apps Script Web App
 *
 * Deployment:
 * 1. Google Sheet ochiladi
 * 2. Extensions -> Apps Script
 * 3. Shu fayl kodini paste qilinadi
 * 4. SECRET o'zgartiriladi
 * 5. Deploy -> New deployment -> Web app
 *    - Execute as: Me
 *    - Who has access: Anyone
 * 6. URL .env ga yoziladi:
 *    GOOGLE_SCRIPT_WEBAPP_URL=<url>
 *    GOOGLE_SCRIPT_SECRET=<secret>
 */

const SECRET = "CHANGE_ME_SECRET";

const KIRIM_SHEET_NAME = "Kirim";
const CHIQIM_SHEET_NAME = "Chiqim";
const PAYMENT_SHEET_NAME = "To'lovlar";

const KIRIM_HEADERS = [
  "Telegram ID",
  "Telefon raqam",
  "Ism",
  "Mahsulot nomi",
  "Kg miqdori",
  "Qutilar soni",
  "1 kg narxi",
  "Umumiy summa",
  "Status",
  "Yaratilgan sana"
];

const CHIQIM_HEADERS = [
  "Product ID",
  "Telegram ID",
  "Telefon raqam",
  "Ism",
  "Mahsulot nomi",
  "Kg miqdori",
  "Qutilar soni",
  "1 kg narxi",
  "Umumiy summa",
  "Chiqim sanasi",
  "Admin Telegram ID",
  "Izoh"
];

const PAYMENT_HEADERS = [
  "Payment ID",
  "Telegram ID",
  "Telefon raqam",
  "Ism",
  "To'lov summasi",
  "Izoh",
  "Admin Telegram ID",
  "Yaratilgan sana"
];

function jsonOutput(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

function getOrCreateSheet_(name, headers) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(name);

  if (!sheet) {
    sheet = ss.insertSheet(name);
  }

  const firstRow = sheet.getRange(1, 1, 1, headers.length).getValues()[0];
  const isEmpty = firstRow.every(cell => cell === "");

  if (isEmpty) {
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
  }

  return sheet;
}

function appendRow_(sheetName, headers, row) {
  if (!Array.isArray(row)) {
    throw new Error("data must be an array");
  }

  const sheet = getOrCreateSheet_(sheetName, headers);

  const normalized = headers.map((_, index) => {
    return row[index] === undefined || row[index] === null ? "" : row[index];
  });

  sheet.appendRow(normalized);
}

function doGet(e) {
  return jsonOutput({
    ok: true,
    service: "ombor_bot_sheets"
  });
}

function doPost(e) {
  try {
    if (!e || !e.postData || !e.postData.contents) {
      return jsonOutput({ ok: false, error: "empty body" });
    }

    const payload = JSON.parse(e.postData.contents);

    if (payload.secret !== SECRET) {
      return jsonOutput({ ok: false, error: "unauthorized" });
    }

    if (payload.action === "append_kirim") {
      appendRow_(KIRIM_SHEET_NAME, KIRIM_HEADERS, payload.data);
      return jsonOutput({ ok: true });
    }

    if (payload.action === "append_chiqim") {
      appendRow_(CHIQIM_SHEET_NAME, CHIQIM_HEADERS, payload.data);
      return jsonOutput({ ok: true });
    }

    if (payload.action === "append_payment") {
      appendRow_(PAYMENT_SHEET_NAME, PAYMENT_HEADERS, payload.data);
      return jsonOutput({ ok: true });
    }

    return jsonOutput({ ok: false, error: "unknown action" });
  } catch (err) {
    return jsonOutput({
      ok: false,
      error: String(err && err.message ? err.message : err)
    });
  }
}
