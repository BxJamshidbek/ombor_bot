from app.services.sheets_service import product_to_sheet_row, HEADERS


def test_headers_structure():
    expected = [
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
    assert HEADERS == expected
    assert len(HEADERS) == 10


def test_product_to_sheet_row_full():
    product = {
        "telegram_id": 123456789,
        "phone": "+998901234567",
        "client_name": "Ali Valiyev",
        "product_name": "Olma",
        "kg_amount": 20.0,
        "price_per_kg": 2000.0,
        "storage_days": 30,
        "total_price": 1200000.0,
        "status": "active",
        "created_at": "2026-07-07T12:00:00",
    }

    row = product_to_sheet_row(product)

    assert row[0] == 123456789
    assert row[1] == "+998901234567"
    assert row[2] == "Ali Valiyev"
    assert row[3] == "Olma"
    assert row[4] == 20.0
    assert row[5] == 2000.0
    assert row[6] == 30
    assert row[7] == 1200000.0
    assert row[8] == "active"
    assert row[9] == "2026-07-07T12:00:00"


def test_product_to_sheet_row_missing_fields():
    product = {
        "telegram_id": 123,
        "phone": "+998901234567",
    }

    row = product_to_sheet_row(product)

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
        "price_per_kg",
        "storage_days",
        "total_price",
        "status",
        "created_at",
    ]

    product = {k: str(i) for i, k in enumerate(columns)}
    row = product_to_sheet_row(product)

    assert row[0] == "0"  # telegram_id
    assert row[3] == "3"  # product_name
    assert row[9] == "9"  # created_at
