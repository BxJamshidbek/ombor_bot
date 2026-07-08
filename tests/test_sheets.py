from app.services.sheets_service import (
    CHIQIM_HEADERS,
    KIRIM_HEADERS,
    PAYMENT_HEADERS,
    exit_to_sheet_row,
    payment_to_sheet_row,
    product_to_sheet_row,
)


def test_kirim_headers_structure():
    expected = [
        "Telegram ID",
        "Telefon raqam",
        "Ism",
        "Mahsulot nomi",
        "Kg miqdori",
        "Qutilar soni",
        "1 kg narxi",
        "Umumiy summa",
        "Status",
        "Yaratilgan sana",
    ]
    assert KIRIM_HEADERS == expected
    assert len(KIRIM_HEADERS) == 10


def test_chiqim_headers_structure():
    expected = [
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
        "Izoh",
    ]
    assert CHIQIM_HEADERS == expected
    assert len(CHIQIM_HEADERS) == 12


def test_payment_headers_structure():
    expected = [
        "Payment ID",
        "Telegram ID",
        "Telefon raqam",
        "Ism",
        "To'lov summasi",
        "Izoh",
        "Admin Telegram ID",
        "Yaratilgan sana",
    ]
    assert PAYMENT_HEADERS == expected
    assert len(PAYMENT_HEADERS) == 8


def test_product_to_sheet_row_full():
    product = {
        "telegram_id": 123456789,
        "phone": "+998901234567",
        "client_name": "Ali Valiyev",
        "product_name": "Olma",
        "kg_amount": 20.0,
        "box_count": 5,
        "price_per_kg": 2000.0,
        "total_price": 40000.0,
        "status": "active",
        "created_at": "2026-07-07T12:00:00",
    }

    row = product_to_sheet_row(product)

    assert len(row) == 10
    assert row[0] == 123456789
    assert row[1] == "+998901234567"
    assert row[2] == "Ali Valiyev"
    assert row[3] == "Olma"
    assert row[4] == 20.0
    assert row[5] == 5
    assert row[6] == 2000.0
    assert row[7] == 40000.0
    assert row[8] == "active"
    assert row[9] == "2026-07-07T12:00:00"


def test_product_to_sheet_row_missing_fields():
    product = {
        "telegram_id": 123,
        "phone": "+998901234567",
    }

    row = product_to_sheet_row(product)

    assert len(row) == 10
    assert row[0] == 123
    assert row[1] == "+998901234567"
    assert row[2] == ""
    assert row[3] == ""
    assert row[4] == 0
    assert row[5] == 0
    assert row[6] == 0
    assert row[7] == 0
    assert row[8] == "active"
    assert isinstance(row[9], str)


def test_product_to_sheet_row_order():
    columns = [
        "telegram_id",
        "phone",
        "client_name",
        "product_name",
        "kg_amount",
        "box_count",
        "price_per_kg",
        "total_price",
        "status",
        "created_at",
    ]

    product = {k: str(i) for i, k in enumerate(columns)}
    row = product_to_sheet_row(product)

    assert row[0] == "0"
    assert row[3] == "3"
    assert row[4] == "4"
    assert row[5] == "5"
    assert row[6] == "6"
    assert row[7] == "7"
    assert row[8] == "8"
    assert row[9] == "9"


def test_exit_to_sheet_row_full():
    exit_data = {
        "product_id": 42,
        "telegram_id": 123456789,
        "phone": "+998901234567",
        "client_name": "Ali Valiyev",
        "product_name": "Olma",
        "kg_amount": 20.0,
        "box_count": 5,
        "price_per_kg": 2000.0,
        "total_price": 40000.0,
        "exited_at": "2026-07-07T12:00:00",
        "created_by_admin_id": 987654321,
        "note": "Mijoz olib ketdi",
    }

    row = exit_to_sheet_row(exit_data)

    assert len(row) == 12
    assert row[0] == 42
    assert row[1] == 123456789
    assert row[2] == "+998901234567"
    assert row[3] == "Ali Valiyev"
    assert row[4] == "Olma"
    assert row[5] == 20.0
    assert row[6] == 5
    assert row[7] == 2000.0
    assert row[8] == 40000.0
    assert row[9] == "2026-07-07T12:00:00"
    assert row[10] == 987654321
    assert row[11] == "Mijoz olib ketdi"


def test_exit_to_sheet_row_note_none():
    exit_data = {
        "product_id": 1,
        "telegram_id": 123,
        "phone": "+998901234567",
        "exited_at": "2026-07-07T12:00:00",
        "created_by_admin_id": 987,
        "note": None,
    }

    row = exit_to_sheet_row(exit_data)

    assert row[0] == 1
    assert row[10] == 987
    assert row[11] == ""


def test_payment_to_sheet_row_full():
    payment = {
        "id": 1,
        "telegram_id": 123456789,
        "phone": "+998901234567",
        "client_name": "Ali Valiyev",
        "amount": 500000.0,
        "note": "Avans",
        "created_by_admin_id": 987654321,
        "created_at": "2026-07-07T12:00:00",
    }

    row = payment_to_sheet_row(payment)

    assert len(row) == 8
    assert row[0] == 1
    assert row[1] == 123456789
    assert row[2] == "+998901234567"
    assert row[3] == "Ali Valiyev"
    assert row[4] == 500000.0
    assert row[5] == "Avans"
    assert row[6] == 987654321
    assert row[7] == "2026-07-07T12:00:00"


def test_payment_to_sheet_row_note_none():
    payment = {
        "id": 2,
        "telegram_id": 123,
        "phone": "+998901234567",
        "amount": 300000.0,
        "created_by_admin_id": 987,
        "created_at": "2026-07-07T12:00:00",
    }

    row = payment_to_sheet_row(payment)

    assert row[0] == 2
    assert row[5] == ""
    assert row[6] == 987
