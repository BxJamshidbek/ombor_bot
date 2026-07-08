from app.services.sheets_service import (
    EXITED_HEADERS,
    MAIN_HEADERS,
    PAYMENT_HISTORY_HEADERS,
    payment_to_history_row,
    product_to_exited_sheet_row,
    product_to_main_sheet_row,
)


def test_main_headers_length():
    assert len(MAIN_HEADERS) == 14


def test_exited_headers_length():
    assert len(EXITED_HEADERS) == 15


def test_payment_history_headers_length():
    assert len(PAYMENT_HISTORY_HEADERS) == 8


def test_no_note_in_main_headers():
    assert "Izoh" not in MAIN_HEADERS


def test_no_note_in_exited_headers():
    assert "Izoh" not in EXITED_HEADERS


def test_no_note_in_payment_history_headers():
    assert "Izoh" not in PAYMENT_HISTORY_HEADERS


def test_product_id_in_payment_history_headers():
    assert "Product ID" in PAYMENT_HISTORY_HEADERS


def test_product_to_main_sheet_row_full():
    product = {
        "id": 42,
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
    row = product_to_main_sheet_row(product)
    assert len(row) == 14
    assert row[0] == 42
    assert row[1] == 123456789
    assert row[4] == "Olma"
    assert row[8] == 40000.0
    assert row[9] == 0
    assert row[10] == 40000.0
    assert row[11] == "active"


def test_product_to_main_sheet_row_no_created_at():
    product = {"id": 1, "product_name": "Olma", "total_price": 20000}
    row = product_to_main_sheet_row(product, paid_amount=0, remaining_amount=20000)
    assert row[12] == ""
    assert len(row) == 14


def test_payment_to_history_row_full():
    payment = {
        "id": 1,
        "product_id": 42,
        "telegram_id": 123456789,
        "phone": "+998901234567",
        "client_name": "Ali Valiyev",
        "amount": 500000.0,
        "created_by_admin_id": 987654321,
        "created_at": "2026-07-07T12:00:00",
    }
    row = payment_to_history_row(payment)
    assert len(row) == 8
    assert row[0] == 1
    assert row[1] == 42
    assert row[2] == 123456789
    assert row[5] == 500000.0
    assert row[6] == 987654321


def test_payment_to_history_row_no_note():
    payment = {"id": 2, "telegram_id": 123, "amount": 300000.0}
    row = payment_to_history_row(payment)
    assert len(row) == 8
    assert row[1] == ""


def test_product_to_exited_sheet_row():
    exit_data = {
        "product_id": 1,
        "telegram_id": 111,
        "phone": "+998901111111",
        "client_name": "Test",
        "product_name": "Banan",
        "kg_amount": 15.0,
        "box_count": 3,
        "price_per_kg": 5000.0,
        "total_price": 75000.0,
        "exited_at": "2026-07-08T15:00:00",
    }
    row = product_to_exited_sheet_row(exit_data, paid_amount=0, remaining_amount=75000)
    assert len(row) == 15
    assert row[0] == 1
    assert row[4] == "Banan"
    assert row[11] == "exited"
    assert row[13] == "2026-07-08T15:00:00"
