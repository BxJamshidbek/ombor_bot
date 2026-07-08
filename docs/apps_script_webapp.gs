/**
 * Ombor Bot — Google Sheets Apps Script Web App
 *
 * 2 ta sheet: Ombor + To'lovlar tarixi
 * 4 ta action: append_product, update_exit, append_payment_history, update_payments
 */

const SECRET = "CHANGE_ME_SECRET";

const MAIN_SHEET_NAME = "Ombor";
const PAYMENT_HISTORY_SHEET_NAME = "To'lovlar tarixi";

const MAIN_HEADERS = [
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
  "Izoh"
];

const PAYMENT_HISTORY_HEADERS = [
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

function getSpreadsheet_() {
  return SpreadsheetApp.getActiveSpreadsheet();
}

function getOrCreateSheet_(name, headers) {
  const ss = getSpreadsheet_();
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

function findRowByProductId_(sheet, productId) {
  const col = 1;
  const values = sheet.getRange(2, col, sheet.getLastRow() - 1, 1).getValues();
  for (let i = 0; i < values.length; i++) {
    if (String(values[i][0]) === String(productId)) {
      return i + 2;
    }
  }
  return null;
}

function appendProduct_(row) {
  const sheet = getOrCreateSheet_(MAIN_SHEET_NAME, MAIN_HEADERS);
  const normalized = MAIN_HEADERS.map((_, index) => {
    return row[index] === undefined || row[index] === null ? "" : row[index];
  });
  sheet.appendRow(normalized);
}

function updateExit_(data) {
  const sheet = getOrCreateSheet_(MAIN_SHEET_NAME, MAIN_HEADERS);
  const row = findRowByProductId_(sheet, data.product_id);
  if (!row) {
    return false;
  }
  sheet.getRange(row, 12).setValue(data.status || "exited");
  sheet.getRange(row, 14).setValue(data.exited_at || "");
  sheet.getRange(row, 15).setValue(data.note || "");
  return true;
}

function appendPaymentHistory_(row) {
  const sheet = getOrCreateSheet_(PAYMENT_HISTORY_SHEET_NAME, PAYMENT_HISTORY_HEADERS);
  const normalized = PAYMENT_HISTORY_HEADERS.map((_, index) => {
    return row[index] === undefined || row[index] === null ? "" : row[index];
  });
  sheet.appendRow(normalized);
}

function updatePayments_(updates) {
  const sheet = getOrCreateSheet_(MAIN_SHEET_NAME, MAIN_HEADERS);
  for (let i = 0; i < updates.length; i++) {
    const u = updates[i];
    const row = findRowByProductId_(sheet, u.product_id);
    if (row) {
      sheet.getRange(row, 10).setValue(u.paid_amount);
      sheet.getRange(row, 11).setValue(u.remaining_amount);
    }
  }
  return true;
}

function doGet(e) {
  return jsonOutput({ ok: true, service: "ombor_bot_sheets" });
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

    if (payload.action === "append_product") {
      appendProduct_(payload.data);
      return jsonOutput({ ok: true });
    }

    if (payload.action === "update_exit") {
      updateExit_(payload.data);
      return jsonOutput({ ok: true });
    }

    if (payload.action === "append_payment_history") {
      appendPaymentHistory_(payload.data);
      return jsonOutput({ ok: true });
    }

    if (payload.action === "update_payments") {
      updatePayments_(payload.data);
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
