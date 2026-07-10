/**
 * Ombor Bot — Google Sheets Apps Script Web App
 *
 * 3 ta sheet: Ombor + Chiqarilganlar + To'lovlar tarixi
 * 4 ta action: append_product, update_product_payment, move_product_to_exited, append_payment_history
 */

const SECRET = "ombor_2026_private_secret";
const SPREADSHEET_ID = "1SVuJsd6h9OXo4MdHnmeO7_hDyD8NxLMSY5AeR1tDie4";

const MAIN_SHEET_NAME = "Ombor";
const EXITED_SHEET_NAME = "Chiqarilganlar";
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
  "Yangilangan sana"
];

const EXITED_HEADERS = [
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
  "Yangilangan sana"
];

const PAYMENT_HISTORY_HEADERS = [
  "Payment ID",
  "Product ID",
  "Telegram ID",
  "Telefon raqam",
  "Ism",
  "To'lov summasi",
  "Admin Telegram ID",
  "Yaratilgan sana"
];

function jsonOutput(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

function getSpreadsheet_() {
  return SpreadsheetApp.openById(SPREADSHEET_ID);
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

function updateProductPayment_(data) {
  const sheet = getOrCreateSheet_(MAIN_SHEET_NAME, MAIN_HEADERS);
  const row = findRowByProductId_(sheet, data.product_id);
  if (!row) {
    return { updated: false };
  }
  sheet.getRange(row, 10).setValue(data.paid_amount);
  sheet.getRange(row, 11).setValue(data.remaining_amount);
  sheet.getRange(row, 14).setValue(data.updated_at || "");
  return { updated: true };
}

function moveProductToExited_(data) {
  const mainSheet = getOrCreateSheet_(MAIN_SHEET_NAME, MAIN_HEADERS);
  const exitedSheet = getOrCreateSheet_(EXITED_SHEET_NAME, EXITED_HEADERS);

  const row = findRowByProductId_(mainSheet, data.product_id);
  if (row) {
    const rowValues = mainSheet.getRange(row, 1, 1, MAIN_HEADERS.length).getValues()[0];
    const exitedRow = rowValues.map(val => val === undefined || val === null ? "" : val);
    exitedRow[11] = "exited";
    exitedRow[13] = data.row ? data.row[13] || "" : "";
    exitedRow[14] = new Date().toISOString();
    exitedSheet.appendRow(exitedRow);
    mainSheet.deleteRow(row);
    return { ok: true, moved: true };
  }

  if (data.row && Array.isArray(data.row)) {
    const normalized = EXITED_HEADERS.map((_, index) => {
      return data.row[index] === undefined || data.row[index] === null ? "" : data.row[index];
    });
    exitedSheet.appendRow(normalized);
    return { ok: true, appended: true };
  }

  return { ok: true, moved: false };
}

function appendPaymentHistory_(row) {
  const sheet = getOrCreateSheet_(PAYMENT_HISTORY_SHEET_NAME, PAYMENT_HISTORY_HEADERS);
  const normalized = PAYMENT_HISTORY_HEADERS.map((_, index) => {
    return row[index] === undefined || row[index] === null ? "" : row[index];
  });
  sheet.appendRow(normalized);
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

    if (!payload || payload.secret !== SECRET) {
      return jsonOutput({ ok: false, error: "unauthorized" });
    }

    if (payload.action === "append_product") {
      appendProduct_(payload.data);
      return jsonOutput({ ok: true });
    }

    if (payload.action === "update_product_payment") {
      const result = updateProductPayment_(payload.data);
      return jsonOutput({ ok: true, ...result });
    }

    if (payload.action === "move_product_to_exited") {
      const result = moveProductToExited_(payload.data);
      return jsonOutput(result);
    }

    if (payload.action === "append_payment_history") {
      appendPaymentHistory_(payload.data);
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
