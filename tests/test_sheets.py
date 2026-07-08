from app.services.sheets_service import (
    MAIN_HEADERS,
    PAYMENT_HISTORY_HEADERS,
    payment_to_history_row,
    product_to_main_sheet_row,
)


def test_main_headers_length():
    assert len(MAIN_HEADERS) == 15


def test_payment_history_headers_length():
    assert len(PAYMENT_HISTORY_HEADERS) == 8


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

    assert len(row) == 15
    assert row[0] == 42
    assert row[1] == 123456789
    assert row[2] == "+998901234567"
    assert row[3] == "Ali Valiyev"
    assert row[4] == "Olma"
    assert row[5] == 20.0
    assert row[6] == 5
    assert row[7] == 2000.0
    assert row[8] == 40000.0
    assert row[9] == 0
    assert row[10] == 40000.0
    assert row[11] == "active"
    assert row[12] == "2026-07-07T12:00:00"
    assert row[13] == ""
    assert row[14] == ""


def test_product_to_main_sheet_row_with_allocation():
    product = {
        "id": 1, "total_price": 40000,
        "created_at": "2026-07-07T12:00:00",
    }
    row = product_to_main_sheet_row(product, paid_amount=15000, remaining_amount=25000)
    assert row[9] == 15000
    assert row[10] == 25000


def test_product_to_main_sheet_row_missing_fields():
    product = {"id": 1, "telegram_id": 123, "phone": "+998901234567"}
    row = product_to_main_sheet_row(product)
    assert len(row) == 15
    assert row[9] == 0
    assert row[10] == 0


def test_product_to_main_sheet_row_no_created_at():
    product = {
        "id": 1,
        "product_name": "Olma",
        "kg_amount": 10,
        "total_price": 20000,
    }
    row = product_to_main_sheet_row(product, paid_amount=0, remaining_amount=20000)
    assert row[12] == ""
    assert len(row) == 15


def test_product_to_main_sheet_row_exited_status():
    product = {
        "id": 1,
        "product_name": "Olma",
        "status": "exited",
        "total_price": 20000,
    }
    row = product_to_main_sheet_row(product, paid_amount=0, remaining_amount=20000)
    assert row[11] == "exited"


def test_update_exit_payload_has_row():
    exit_data = {
        "product_id": 42,
        "id": 42,
        "telegram_id": 123456789,
        "phone": "+998901234567",
        "client_name": "Ali Valiyev",
        "product_name": "Olma",
        "kg_amount": 20.0,
        "box_count": 5,
        "price_per_kg": 2000.0,
        "total_price": 40000.0,
        "status": "exited",
        "exited_at": "2026-07-08T12:00:00",
        "note": "Yetkazildi",
    }
    row = product_to_main_sheet_row(
        exit_data, paid_amount=0, remaining_amount=exit_data["total_price"]
    )
    assert len(row) == 15
    assert row[0] == 42
    assert row[11] == "exited"
    assert row[14] == ""


def test_update_exit_payload_row_values():
    exit_data = {
        "product_id": 1,
        "id": 1,
        "telegram_id": 111,
        "phone": "+998901111111",
        "client_name": "Test",
        "product_name": "Banan",
        "kg_amount": 15.0,
        "box_count": 3,
        "price_per_kg": 5000.0,
        "total_price": 75000.0,
        "status": "exited",
        "exited_at": "2026-07-08T15:00:00",
        "note": "Tez orqali",
    }
    row = product_to_main_sheet_row(
        exit_data, paid_amount=0, remaining_amount=75000
    )
    assert row[0] == 1
    assert row[4] == "Banan"
    assert row[5] == 15.0
    assert row[8] == 75000.0
    assert row[9] == 0
    assert row[10] == 75000
    assert row[11] == "exited"
    assert row[12] == ""


def test_payment_to_history_row_full():
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
    row = payment_to_history_row(payment)
    assert len(row) == 8
    assert row[0] == 1
    assert row[1] == 123456789
    assert row[2] == "+998901234567"
    assert row[3] == "Ali Valiyev"
    assert row[4] == 500000.0
    assert row[5] == "Avans"
    assert row[6] == 987654321
    assert row[7] == "2026-07-07T12:00:00"


def test_payment_to_history_row_note_none():
    payment = {"id": 2, "telegram_id": 123, "amount": 300000.0}
    row = payment_to_history_row(payment)
    assert row[5] == ""
